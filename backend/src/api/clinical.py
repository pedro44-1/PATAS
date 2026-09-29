from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session, joinedload

from src.core.database import get_db
from src.core.deps import CurrentUser, require_permission
from src.models.appointment import Appointment
from src.models.medication import Medication, MedicationStatus
from src.models.pet import Pet
from src.models.user import User, UserRole
from src.models.vaccination import Vaccination, VaccinationStatus
from src.schemas.clinical import (
    ClinicalVoidRequest,
    MedicationCreate,
    MedicationResponse,
    MedicationUpdate,
    VaccinationCreate,
    VaccinationResponse,
    VaccinationUpdate,
)
from src.services.audit import audit

router = APIRouter()


def _pet_or_404(db: Session, clinic_id: int, pet_id: int) -> Pet:
    pet = db.query(Pet).filter(
        Pet.id == pet_id,
        Pet.clinic_id == clinic_id,
        Pet.archived_at.is_(None),
        Pet.owner.has(archived_at=None),
    ).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    return pet


def _vet_or_422(db: Session, clinic_id: int, vet_id: int) -> User:
    vet = db.query(User).filter(
        User.id == vet_id,
        User.clinic_id == clinic_id,
        User.role.in_([UserRole.VET, UserRole.ADMIN]),
    ).first()
    if not vet:
        raise HTTPException(status_code=422, detail="O responsável deve ser um veterinário da clínica")
    return vet


def _appointment_or_422(
    db: Session,
    clinic_id: int,
    pet_id: int,
    appointment_id: int | None,
) -> Appointment | None:
    if appointment_id is None:
        return None
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.clinic_id == clinic_id,
    ).first()
    if not appointment:
        raise HTTPException(status_code=422, detail="A consulta não pertence à clínica")
    if appointment.pet_id != pet_id:
        raise HTTPException(status_code=422, detail="A consulta não pertence ao animal")
    return appointment


def _vaccination_payload(record: Vaccination) -> dict:
    return {
        "id": record.id,
        "clinic_id": record.clinic_id,
        "pet_id": record.pet_id,
        "appointment_id": record.appointment_id,
        "vet_id": record.vet_id,
        "vet_name": record.vet.name if record.vet else None,
        "name": record.name,
        "administered_at": record.administered_at,
        "dose": record.dose,
        "lot_number": record.lot_number,
        "expires_at": record.expires_at,
        "next_due_at": record.next_due_at,
        "notes": record.notes,
        "status": record.status,
        "void_reason": record.void_reason,
        "voided_at": record.voided_at,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def _medication_payload(record: Medication) -> dict:
    return {
        "id": record.id,
        "clinic_id": record.clinic_id,
        "pet_id": record.pet_id,
        "appointment_id": record.appointment_id,
        "vet_id": record.vet_id,
        "vet_name": record.vet.name if record.vet else None,
        "name": record.name,
        "dosage": record.dosage,
        "frequency": record.frequency,
        "route": record.route,
        "start_date": record.start_date,
        "end_date": record.end_date,
        "instructions": record.instructions,
        "notes": record.notes,
        "status": record.status,
        "void_reason": record.void_reason,
        "voided_at": record.voided_at,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


@router.get("/vaccinations/", response_model=list[VaccinationResponse])
def list_vaccinations(
    response: Response,
    skip: int = 0,
    limit: int = 100,
    pet_id: int | None = None,
    current_user: CurrentUser = Depends(require_permission("clinical:read")),
    db: Session = Depends(get_db),
):
    query = db.query(Vaccination).options(joinedload(Vaccination.vet)).filter(
        Vaccination.clinic_id == current_user.clinic_id,
    )
    if pet_id is not None:
        query = query.filter(Vaccination.pet_id == pet_id)
    total = query.count()
    records = query.order_by(Vaccination.administered_at.desc()).offset(skip).limit(limit).all()
    response.headers["X-Total-Count"] = str(total)
    return [_vaccination_payload(record) for record in records]


@router.post("/vaccinations/", response_model=VaccinationResponse)
def create_vaccination(
    data: VaccinationCreate,
    current_user: CurrentUser = Depends(require_permission("clinical:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    _pet_or_404(db, current_user.clinic_id, data.pet_id)
    _vet_or_422(db, current_user.clinic_id, data.vet_id)
    _appointment_or_422(db, current_user.clinic_id, data.pet_id, data.appointment_id)

    record = Vaccination(clinic_id=current_user.clinic_id, **data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="CREATE",
        resource="vaccination",
        resource_id=record.id,
        details={"pet_id": record.pet_id, "name": record.name, "vet_id": record.vet_id},
        ip_address=request.client.host if request else None,
    )
    db.refresh(record)
    return _vaccination_payload(record)


@router.patch("/vaccinations/{vaccination_id}", response_model=VaccinationResponse)
def update_vaccination(
    vaccination_id: int,
    data: VaccinationUpdate,
    current_user: CurrentUser = Depends(require_permission("clinical:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    record = db.query(Vaccination).options(joinedload(Vaccination.vet)).filter(
        Vaccination.id == vaccination_id,
        Vaccination.clinic_id == current_user.clinic_id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Vacina não encontrada")
    if record.status == VaccinationStatus.VOIDED:
        raise HTTPException(status_code=409, detail="Uma vacina anulada não pode ser alterada")

    updates = data.model_dump(exclude_unset=True)
    _vet_or_422(db, current_user.clinic_id, updates.get("vet_id", record.vet_id))
    _appointment_or_422(
        db,
        current_user.clinic_id,
        record.pet_id,
        updates.get("appointment_id", record.appointment_id),
    )
    for key, value in updates.items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="UPDATE",
        resource="vaccination",
        resource_id=record.id,
        details=updates,
        ip_address=request.client.host if request else None,
    )
    db.refresh(record)
    return _vaccination_payload(record)


@router.post("/vaccinations/{vaccination_id}/void", response_model=VaccinationResponse)
def void_vaccination(
    vaccination_id: int,
    data: ClinicalVoidRequest,
    current_user: CurrentUser = Depends(require_permission("clinical:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    record = db.query(Vaccination).options(joinedload(Vaccination.vet)).filter(
        Vaccination.id == vaccination_id,
        Vaccination.clinic_id == current_user.clinic_id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Vacina não encontrada")
    if record.status == VaccinationStatus.VOIDED:
        raise HTTPException(status_code=409, detail="A vacina já está anulada")
    reason = data.reason.strip()
    if not reason:
        raise HTTPException(status_code=422, detail="O motivo da anulação é obrigatório")

    record.status = VaccinationStatus.VOIDED
    record.void_reason = reason
    record.voided_at = datetime.now(UTC)
    record.voided_by = current_user.id
    db.commit()
    db.refresh(record)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="VOID",
        resource="vaccination",
        resource_id=record.id,
        details={"reason": reason},
        ip_address=request.client.host if request else None,
    )
    db.refresh(record)
    return _vaccination_payload(record)


@router.get("/medications/", response_model=list[MedicationResponse])
def list_medications(
    response: Response,
    skip: int = 0,
    limit: int = 100,
    pet_id: int | None = None,
    current_user: CurrentUser = Depends(require_permission("clinical:read")),
    db: Session = Depends(get_db),
):
    query = db.query(Medication).options(joinedload(Medication.vet)).filter(
        Medication.clinic_id == current_user.clinic_id,
    )
    if pet_id is not None:
        query = query.filter(Medication.pet_id == pet_id)
    total = query.count()
    records = query.order_by(Medication.start_date.desc(), Medication.created_at.desc()).offset(skip).limit(limit).all()
    response.headers["X-Total-Count"] = str(total)
    return [_medication_payload(record) for record in records]


@router.post("/medications/", response_model=MedicationResponse)
def create_medication(
    data: MedicationCreate,
    current_user: CurrentUser = Depends(require_permission("clinical:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    _pet_or_404(db, current_user.clinic_id, data.pet_id)
    _vet_or_422(db, current_user.clinic_id, data.vet_id)
    _appointment_or_422(db, current_user.clinic_id, data.pet_id, data.appointment_id)
    if data.end_date and data.end_date < data.start_date:
        raise HTTPException(status_code=422, detail="A data de fim não pode ser anterior à data de início")

    record = Medication(clinic_id=current_user.clinic_id, **data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="CREATE",
        resource="medication",
        resource_id=record.id,
        details={"pet_id": record.pet_id, "name": record.name, "vet_id": record.vet_id},
        ip_address=request.client.host if request else None,
    )
    db.refresh(record)
    return _medication_payload(record)


@router.patch("/medications/{medication_id}", response_model=MedicationResponse)
def update_medication(
    medication_id: int,
    data: MedicationUpdate,
    current_user: CurrentUser = Depends(require_permission("clinical:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    record = db.query(Medication).options(joinedload(Medication.vet)).filter(
        Medication.id == medication_id,
        Medication.clinic_id == current_user.clinic_id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")
    if record.status == MedicationStatus.VOIDED:
        raise HTTPException(status_code=409, detail="Um medicamento anulado não pode ser alterado")

    updates = data.model_dump(exclude_unset=True)
    _vet_or_422(db, current_user.clinic_id, updates.get("vet_id", record.vet_id))
    _appointment_or_422(
        db,
        current_user.clinic_id,
        record.pet_id,
        updates.get("appointment_id", record.appointment_id),
    )
    start_date = updates.get("start_date", record.start_date)
    end_date = updates.get("end_date", record.end_date)
    if end_date and end_date < start_date:
        raise HTTPException(status_code=422, detail="A data de fim não pode ser anterior à data de início")
    if updates.get("status") == MedicationStatus.VOIDED:
        raise HTTPException(status_code=422, detail="Use o endpoint de anulação para invalidar um medicamento")

    for key, value in updates.items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="UPDATE",
        resource="medication",
        resource_id=record.id,
        details=updates,
        ip_address=request.client.host if request else None,
    )
    db.refresh(record)
    return _medication_payload(record)


@router.post("/medications/{medication_id}/void", response_model=MedicationResponse)
def void_medication(
    medication_id: int,
    data: ClinicalVoidRequest,
    current_user: CurrentUser = Depends(require_permission("clinical:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    record = db.query(Medication).options(joinedload(Medication.vet)).filter(
        Medication.id == medication_id,
        Medication.clinic_id == current_user.clinic_id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")
    if record.status == MedicationStatus.VOIDED:
        raise HTTPException(status_code=409, detail="O medicamento já está anulado")
    reason = data.reason.strip()
    if not reason:
        raise HTTPException(status_code=422, detail="O motivo da anulação é obrigatório")

    record.status = MedicationStatus.VOIDED
    record.void_reason = reason
    record.voided_at = datetime.now(UTC)
    record.voided_by = current_user.id
    db.commit()
    db.refresh(record)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="VOID",
        resource="medication",
        resource_id=record.id,
        details={"reason": reason},
        ip_address=request.client.host if request else None,
    )
    db.refresh(record)
    return _medication_payload(record)
