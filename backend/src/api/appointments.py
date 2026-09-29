
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from src.core.database import get_db
from src.core.deps import CurrentUser, get_current_user
from src.core.timezones import local_day_bounds, utc_naive
from src.models.appointment import Appointment, AppointmentStatus
from src.models.pet import Pet
from src.models.service_type import ServiceType
from src.models.user import User, UserRole
from src.schemas.appointment import AppointmentCreate, AppointmentResponse, AppointmentUpdate
from src.services.appointment_lifecycle import (
    ensure_no_appointment_conflict,
    transition_appointment,
)
from src.services.audit import audit

router = APIRouter()


@router.get("/vets")
def list_clinic_vets(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(User).filter(
        User.clinic_id == current_user.clinic_id,
        User.role.in_([UserRole.VET, UserRole.ADMIN]),
    ).order_by(User.name).all()


def _validate_vet(db: Session, clinic_id: int, vet_id: int) -> User:
    vet = db.query(User).filter(
        User.id == vet_id,
        User.clinic_id == clinic_id,
        User.role.in_([UserRole.VET, UserRole.ADMIN]),
    ).first()
    if not vet:
        raise HTTPException(status_code=422, detail="O veterinário não pertence à clínica")
    return vet


def _validate_service_type(db: Session, clinic_id: int, service_type_id: int | None) -> ServiceType | None:
    if service_type_id is None:
        return None
    service_type = db.query(ServiceType).filter(
        ServiceType.id == service_type_id,
        ServiceType.clinic_id == clinic_id,
        ServiceType.active.is_(True),
    ).first()
    if not service_type:
        raise HTTPException(status_code=422, detail="O tipo de serviço não pertence à clínica ou está inativo")
    return service_type


@router.get("/", response_model=list[AppointmentResponse])
def list_appointments(
    date: str | None = None,
    skip: int = 0,
    limit: int = 100,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Appointment).options(
        joinedload(Appointment.pet),
        joinedload(Appointment.owner),
        joinedload(Appointment.vet),
    ).filter(Appointment.clinic_id == current_user.clinic_id)
    if date:
        start, end = local_day_bounds(date, error_detail="A data da agenda é inválida")
        query = query.filter(
            Appointment.scheduled_at >= start,
            Appointment.scheduled_at < end,
        )
    return query.order_by(Appointment.scheduled_at).offset(skip).limit(limit).all()


@router.post("/", response_model=AppointmentResponse)
def create_appointment(
    data: AppointmentCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    if data.weight is not None and current_user.role not in {UserRole.VET, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail="Apenas veterinários podem registar o peso clínico")
    pet = db.query(Pet).filter(
        Pet.id == data.pet_id,
        Pet.clinic_id == current_user.clinic_id,
        Pet.archived_at.is_(None),
        Pet.owner.has(archived_at=None),
    ).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Animal não encontrado")

    _validate_vet(db, current_user.clinic_id, data.vet_id)
    _validate_service_type(db, current_user.clinic_id, data.service_type_id)
    ensure_no_appointment_conflict(
        db,
        current_user.clinic_id,
        data.vet_id,
        data.scheduled_at,
        data.duration_min,
    )
    appt_data = data.model_dump()
    appt_data["scheduled_at"] = utc_naive(appt_data["scheduled_at"])
    appt_data["owner_id"] = pet.owner_id
    appt = Appointment(clinic_id=current_user.clinic_id, **appt_data)
    db.add(appt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="O veterinário já tem uma consulta nesse horário")
    db.refresh(appt)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="CREATE",
        resource="appointment",
        resource_id=appt.id,
        details={"pet_id": appt.pet_id, "vet_id": appt.vet_id, "scheduled_at": str(appt.scheduled_at)},
        ip_address=request.client.host if request else None,
    )
    return appt


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    appt = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.clinic_id == current_user.clinic_id,
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")
    return appt


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    appt = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.clinic_id == current_user.clinic_id,
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")
    updates = data.model_dump(exclude_unset=True)
    next_status = updates.pop("status", None)
    status_reason = updates.pop("status_reason", None)
    if status_reason is not None and next_status is None:
        raise HTTPException(status_code=422, detail="O motivo só pode ser alterado numa transição de estado")
    current_status = AppointmentStatus(appt.status)
    if current_status in {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW}:
        raise HTTPException(status_code=409, detail="Esta consulta já não pode ser alterada")

    scheduling_fields = {"pet_id", "vet_id", "scheduled_at", "duration_min", "reason", "notes", "service_type_id"}
    if current_status != AppointmentStatus.SCHEDULED and scheduling_fields.intersection(updates):
        raise HTTPException(status_code=409, detail="A agenda só pode ser alterada antes do início do atendimento")
    if "weight" in updates and current_user.role not in {UserRole.VET, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail="Apenas veterinários podem registar o peso clínico")

    if "pet_id" in updates:
        pet = db.query(Pet).filter(
            Pet.id == updates["pet_id"],
            Pet.clinic_id == current_user.clinic_id,
            Pet.archived_at.is_(None),
            Pet.owner.has(archived_at=None),
        ).first()
        if not pet:
            raise HTTPException(status_code=404, detail="Animal não encontrado")
        updates["owner_id"] = pet.owner_id
    next_vet_id = updates.get("vet_id", appt.vet_id)
    if "service_type_id" in updates:
        _validate_service_type(db, current_user.clinic_id, updates["service_type_id"])
    next_scheduled_at = updates.get("scheduled_at", appt.scheduled_at)
    next_duration = updates.get("duration_min", appt.duration_min or 30)
    _validate_vet(db, current_user.clinic_id, next_vet_id)
    if {"scheduled_at", "duration_min", "vet_id"}.intersection(updates):
        ensure_no_appointment_conflict(db, current_user.clinic_id, next_vet_id, next_scheduled_at, next_duration, appt.id)
        if "scheduled_at" in updates:
            updates["scheduled_at"] = utc_naive(next_scheduled_at)
    for key, value in updates.items():
        setattr(appt, key, value)
    if next_status is not None:
        transition_appointment(
            db,
            appt,
            next_status,
            reason=status_reason,
            actor_role=current_user.role,
        )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="O veterinário já tem uma consulta nesse horário")
    db.refresh(appt)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="UPDATE",
        resource="appointment",
        resource_id=appt.id,
        details={**updates, "status": next_status.value if next_status else None, "status_reason": status_reason},
        ip_address=request.client.host if request else None,
    )
    return appt


@router.delete("/{appointment_id}", response_model=AppointmentResponse)
def delete_appointment(
    appointment_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    appt = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.clinic_id == current_user.clinic_id,
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")
    if appt.status != AppointmentStatus.SCHEDULED:
        raise HTTPException(status_code=409, detail="Consultas iniciadas ou concluídas não podem ser apagadas")
    transition_appointment(
        db,
        appt,
        AppointmentStatus.CANCELLED,
        reason="Consulta removida pela clínica",
        actor_role=current_user.role,
    )
    db.commit()
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="UPDATE",
        resource="appointment",
        resource_id=appointment_id,
        details={"status": AppointmentStatus.CANCELLED.value, "status_reason": appt.status_reason},
        ip_address=request.client.host if request else None,
    )
    return appt
