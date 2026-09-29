from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload

from src.core.database import get_db
from src.core.deps import CurrentUser, require_permission
from src.models.appointment import Appointment
from src.models.clinical_exam import ClinicalExamFinding, ClinicalExamObservation, ExamFindingStatus
from src.models.medication import Medication, MedicationStatus
from src.models.treatment import Treatment
from src.models.user import User, UserRole
from src.schemas.clinical import MedicationResponse
from src.schemas.encounter import (
    ClinicalRecordResponse,
    ClinicalRecordUpdate,
    ClinicalTreatmentResponse,
)
from src.schemas.exam_catalog import ExamObservationResponse
from src.services.audit import audit

router = APIRouter()


def _appointment_or_404(db: Session, clinic_id: int, appointment_id: int) -> Appointment:
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.clinic_id == clinic_id,
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")
    return appointment


def _vet_or_422(db: Session, clinic_id: int, vet_id: int | None) -> None:
    if vet_id is None:
        return
    vet = db.query(User).filter(
        User.id == vet_id,
        User.clinic_id == clinic_id,
        User.role.in_([UserRole.VET, UserRole.ADMIN]),
    ).first()
    if not vet:
        raise HTTPException(status_code=422, detail="O veterinário referenciador não pertence à clínica")


def _medication_response(record: Medication) -> MedicationResponse:
    return MedicationResponse(
        id=record.id,
        clinic_id=record.clinic_id,
        pet_id=record.pet_id,
        appointment_id=record.appointment_id,
        vet_id=record.vet_id,
        vet_name=record.vet.name if record.vet else None,
        name=record.name,
        dosage=record.dosage,
        frequency=record.frequency,
        route=record.route,
        start_date=record.start_date,
        end_date=record.end_date,
        instructions=record.instructions,
        notes=record.notes,
        status=record.status,
        void_reason=record.void_reason,
        voided_at=record.voided_at,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _treatment_response(record: Treatment | None) -> ClinicalTreatmentResponse | None:
    if record is None:
        return None
    return ClinicalTreatmentResponse(
        id=record.id,
        appointment_id=record.appointment_id,
        diagnosis=record.diagnosis,
        notes=record.notes,
        prescription=record.prescription,
        anamnesis=record.anamnesis,
        consultation_type=record.consultation_type,
        referring_vet_id=record.referring_vet_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _observation_response(record: ClinicalExamObservation) -> ExamObservationResponse:
    finding = record.finding
    system = finding.system if finding else None
    return ExamObservationResponse(
        id=record.id,
        appointment_id=record.appointment_id,
        finding_id=record.finding_id,
        finding_name=record.finding_name,
        system_id=finding.system_id if finding else 0,
        system_name=system.name if system else "",
        status=record.status,
        note=record.note,
    )


def _record_response(db: Session, appointment: Appointment) -> ClinicalRecordResponse:
    medications = db.query(Medication).options(joinedload(Medication.vet)).filter(
        Medication.clinic_id == appointment.clinic_id,
        Medication.appointment_id == appointment.id,
    ).order_by(Medication.start_date.desc(), Medication.created_at.desc()).all()
    observations = db.query(ClinicalExamObservation).options(
        joinedload(ClinicalExamObservation.finding).joinedload(ClinicalExamFinding.system),
    ).filter(
        ClinicalExamObservation.clinic_id == appointment.clinic_id,
        ClinicalExamObservation.appointment_id == appointment.id,
    ).order_by(ClinicalExamObservation.id).all()
    return ClinicalRecordResponse(
        appointment_id=appointment.id,
        treatment=_treatment_response(appointment.treatment),
        exam_findings=[_observation_response(observation) for observation in observations],
        medications=[_medication_response(medication) for medication in medications],
    )


@router.get("/{appointment_id}/clinical-record", response_model=ClinicalRecordResponse)
def get_clinical_record(
    appointment_id: int,
    current_user: CurrentUser = Depends(require_permission("clinical:read")),
    db: Session = Depends(get_db),
):
    appointment = db.query(Appointment).options(joinedload(Appointment.treatment)).filter(
        Appointment.id == appointment_id,
        Appointment.clinic_id == current_user.clinic_id,
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")
    return _record_response(db, appointment)


@router.put("/{appointment_id}/clinical-record", response_model=ClinicalRecordResponse)
def save_clinical_record(
    appointment_id: int,
    data: ClinicalRecordUpdate,
    current_user: CurrentUser = Depends(require_permission("clinical:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    appointment = _appointment_or_404(db, current_user.clinic_id, appointment_id)
    _vet_or_422(db, current_user.clinic_id, data.referring_vet_id)

    treatment = appointment.treatment
    if treatment is None:
        treatment = Treatment(clinic_id=current_user.clinic_id, appointment_id=appointment.id)
        db.add(treatment)
    for key in ("anamnesis", "diagnosis", "notes", "prescription", "consultation_type", "referring_vet_id"):
        setattr(treatment, key, getattr(data, key))

    for observation_input in data.exam_findings:
        finding = db.query(ClinicalExamFinding).options(
            joinedload(ClinicalExamFinding.system),
        ).filter(
            ClinicalExamFinding.id == observation_input.finding_id,
            ClinicalExamFinding.clinic_id == current_user.clinic_id,
        ).first()
        if not finding:
            raise HTTPException(status_code=422, detail="Um dos achados clínicos não pertence à clínica")
        observation = db.query(ClinicalExamObservation).filter(
            ClinicalExamObservation.clinic_id == current_user.clinic_id,
            ClinicalExamObservation.appointment_id == appointment.id,
            ClinicalExamObservation.finding_id == finding.id,
        ).first()
        if observation_input.status == ExamFindingStatus.NOT_EVALUATED:
            if observation:
                db.delete(observation)
            continue
        if observation is None:
            observation = ClinicalExamObservation(
                clinic_id=current_user.clinic_id,
                appointment_id=appointment.id,
                finding_id=finding.id,
                finding_name=finding.name,
            )
            db.add(observation)
        observation.finding_name = finding.name
        observation.status = observation_input.status.value
        observation.note = observation_input.note

    for medication_line in data.medications:
        if medication_line.end_date and medication_line.end_date < medication_line.start_date:
            raise HTTPException(status_code=422, detail="A data de fim de um medicamento não pode ser anterior à data de início")
        medication = None
        if medication_line.id is not None:
            medication = db.query(Medication).filter(
                Medication.id == medication_line.id,
                Medication.clinic_id == current_user.clinic_id,
                Medication.appointment_id == appointment.id,
            ).first()
            if not medication:
                raise HTTPException(status_code=404, detail="Medicamento da prescrição não encontrado")
            if medication.status == MedicationStatus.VOIDED:
                raise HTTPException(status_code=409, detail="Um medicamento anulado não pode ser alterado")
        if medication is None:
            medication = Medication(
                clinic_id=current_user.clinic_id,
                pet_id=appointment.pet_id,
                appointment_id=appointment.id,
                vet_id=appointment.vet_id,
                status=MedicationStatus.ACTIVE,
            )
            db.add(medication)
        for key in ("name", "dosage", "frequency", "route", "start_date", "end_date", "instructions", "notes"):
            setattr(medication, key, getattr(medication_line, key))

    db.commit()
    db.refresh(appointment)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="UPDATE",
        resource="clinical_record",
        resource_id=appointment.id,
        details={"exam_findings": len(data.exam_findings), "medications": len(data.medications)},
        ip_address=request.client.host if request else None,
    )
    return _record_response(db, appointment)
