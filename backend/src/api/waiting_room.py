from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from src.core.database import get_db
from src.core.deps import CurrentUser, require_permission
from src.core.timezones import local_day_bounds, utc_naive
from src.models.appointment import Appointment, AppointmentStatus
from src.models.owner import Owner
from src.models.pet import Pet
from src.models.service_type import ServiceType
from src.models.user import User, UserRole
from src.models.waiting_room import WaitingRoomEntry, WaitingRoomStatus
from src.schemas.waiting_room import (
    WaitingRoomEntryCreate,
    WaitingRoomEntryResponse,
    WaitingRoomEntryUpdate,
    WaitingRoomTransition,
)
from src.services.appointment_lifecycle import (
    ensure_no_appointment_conflict,
    transition_waiting_room,
)
from src.services.audit import audit
from src.services.clinical_catalog import ensure_clinic_defaults

router = APIRouter()


def _day_bounds(value: str | None) -> tuple[datetime, datetime]:
    return local_day_bounds(value, error_detail="A data da sala de espera é inválida")


def _appointment_or_404(db: Session, clinic_id: int, appointment_id: int) -> Appointment:
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.clinic_id == clinic_id,
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")
    return appointment


def _service_type_or_422(db: Session, clinic_id: int, service_type_id: int | None) -> ServiceType:
    ensure_clinic_defaults(db, clinic_id)
    service_type = None
    if service_type_id is not None:
        service_type = db.query(ServiceType).filter(
            ServiceType.id == service_type_id,
            ServiceType.clinic_id == clinic_id,
            ServiceType.active.is_(True),
        ).first()
    if service_type is None:
        service_type = db.query(ServiceType).filter(
            ServiceType.clinic_id == clinic_id,
            ServiceType.slug == "consulta",
            ServiceType.active.is_(True),
        ).first()
    if not service_type:
        raise HTTPException(status_code=422, detail="Tipo de serviço inválido")
    return service_type


def _vet_or_422(db: Session, clinic_id: int, vet_id: int) -> User:
    vet = db.query(User).filter(
        User.id == vet_id,
        User.clinic_id == clinic_id,
        User.role.in_([UserRole.VET, UserRole.ADMIN]),
    ).first()
    if not vet:
        raise HTTPException(status_code=422, detail="O veterinário não pertence à clínica")
    return vet


def _entry_response(entry: WaitingRoomEntry) -> WaitingRoomEntryResponse:
    appointment = entry.appointment
    return WaitingRoomEntryResponse(
        id=entry.id,
        clinic_id=entry.clinic_id,
        appointment_id=appointment.id,
        pet_id=appointment.pet_id,
        pet_name=appointment.pet.name,
        owner_id=appointment.owner_id,
        owner_name=appointment.owner.name,
        vet_id=appointment.vet_id,
        vet_name=appointment.vet.name,
        service_type_id=appointment.service_type_id,
        service_type_name=appointment.service_type.name if appointment.service_type else None,
        scheduled_at=appointment.scheduled_at,
        status=entry.status,
        arrival_at=entry.arrival_at,
        called_at=entry.called_at,
        started_at=entry.started_at,
        completed_at=entry.completed_at,
        room=entry.room,
        message=entry.message,
        status_reason=entry.status_reason,
        reason=appointment.reason,
        notes=appointment.notes,
    )


def _entry_query(db: Session, clinic_id: int):
    return db.query(WaitingRoomEntry).options(
        joinedload(WaitingRoomEntry.appointment).joinedload(Appointment.pet),
        joinedload(WaitingRoomEntry.appointment).joinedload(Appointment.owner),
        joinedload(WaitingRoomEntry.appointment).joinedload(Appointment.vet),
        joinedload(WaitingRoomEntry.appointment).joinedload(Appointment.service_type),
    ).filter(WaitingRoomEntry.clinic_id == clinic_id)


@router.get("/", response_model=list[WaitingRoomEntryResponse])
def list_waiting_room(
    date: str | None = None,
    status: WaitingRoomStatus | None = None,
    service_type_id: int | None = None,
    q: str | None = None,
    current_user: CurrentUser = Depends(require_permission("waiting:read")),
    db: Session = Depends(get_db),
):
    start, end = _day_bounds(date)
    query = _entry_query(db, current_user.clinic_id).filter(
        WaitingRoomEntry.arrival_at >= start,
        WaitingRoomEntry.arrival_at < end,
    )
    if status:
        query = query.filter(WaitingRoomEntry.status == status.value)
    if service_type_id:
        query = query.filter(WaitingRoomEntry.appointment.has(Appointment.service_type_id == service_type_id))
    if q:
        query = query.join(WaitingRoomEntry.appointment).join(Appointment.pet).join(Appointment.owner).filter(
            (Pet.name.ilike(f"%{q}%")) | (Owner.name.ilike(f"%{q}%")),
        )
    entries = query.order_by(WaitingRoomEntry.arrival_at, WaitingRoomEntry.id).all()
    return [_entry_response(entry) for entry in entries]


@router.post("/entries", response_model=WaitingRoomEntryResponse)
def create_waiting_entry(
    data: WaitingRoomEntryCreate,
    current_user: CurrentUser = Depends(require_permission("waiting:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    if data.appointment_id is None and (data.pet_id is None or data.vet_id is None):
        raise HTTPException(status_code=422, detail="Indique uma consulta ou animal e veterinário para a entrada")

    if data.appointment_id is not None:
        appointment = _appointment_or_404(db, current_user.clinic_id, data.appointment_id)
        if appointment.status != AppointmentStatus.SCHEDULED:
            raise HTTPException(status_code=409, detail="Apenas consultas agendadas podem entrar na fila")
        service_type = _service_type_or_422(db, current_user.clinic_id, data.service_type_id or appointment.service_type_id)
        if appointment.service_type_id is None:
            appointment.service_type_id = service_type.id
    else:
        pet = db.query(Pet).filter(
            Pet.id == data.pet_id,
            Pet.clinic_id == current_user.clinic_id,
            Pet.archived_at.is_(None),
            Pet.owner.has(archived_at=None),
        ).first()
        if not pet:
            raise HTTPException(status_code=404, detail="Animal não encontrado")
        _vet_or_422(db, current_user.clinic_id, data.vet_id)
        service_type = _service_type_or_422(db, current_user.clinic_id, data.service_type_id)
        scheduled_at = utc_naive(data.scheduled_at or datetime.now(UTC))
        ensure_no_appointment_conflict(
            db,
            current_user.clinic_id,
            data.vet_id,
            scheduled_at,
            data.duration_min,
        )
        appointment = Appointment(
            clinic_id=current_user.clinic_id,
            pet_id=pet.id,
            owner_id=pet.owner_id,
            vet_id=data.vet_id,
            service_type_id=service_type.id,
            scheduled_at=scheduled_at,
            duration_min=data.duration_min,
            reason=data.reason or service_type.name,
            notes=data.notes,
            status=AppointmentStatus.SCHEDULED,
        )
        db.add(appointment)
        db.flush()

    existing = db.query(WaitingRoomEntry).filter(
        WaitingRoomEntry.clinic_id == current_user.clinic_id,
        WaitingRoomEntry.appointment_id == appointment.id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Esta consulta já está na sala de espera")

    entry = WaitingRoomEntry(
        clinic_id=current_user.clinic_id,
        appointment_id=appointment.id,
        room=data.room,
        message=data.message,
        arrival_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(entry)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A consulta já está na fila ou o veterinário tem outro atendimento")
    db.refresh(entry)
    audit(db, clinic_id=current_user.clinic_id, user_id=current_user.id, action="CREATE", resource="waiting_room_entry", resource_id=entry.id, details={"appointment_id": appointment.id, "status": entry.status}, ip_address=request.client.host if request else None)
    entry = _entry_query(db, current_user.clinic_id).filter(WaitingRoomEntry.id == entry.id).first()
    return _entry_response(entry)


@router.patch("/entries/{entry_id}", response_model=WaitingRoomEntryResponse)
def update_waiting_entry(
    entry_id: int,
    data: WaitingRoomEntryUpdate,
    current_user: CurrentUser = Depends(require_permission("waiting:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    entry = _entry_query(db, current_user.clinic_id).filter(WaitingRoomEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada da sala de espera não encontrada")
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    audit(db, clinic_id=current_user.clinic_id, user_id=current_user.id, action="UPDATE", resource="waiting_room_entry", resource_id=entry.id, details=updates, ip_address=request.client.host if request else None)
    entry = _entry_query(db, current_user.clinic_id).filter(WaitingRoomEntry.id == entry.id).first()
    return _entry_response(entry)


@router.post("/entries/{entry_id}/transition", response_model=WaitingRoomEntryResponse)
def transition_waiting_entry(
    entry_id: int,
    data: WaitingRoomTransition,
    current_user: CurrentUser = Depends(require_permission("waiting:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    entry = _entry_query(db, current_user.clinic_id).filter(WaitingRoomEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada da sala de espera não encontrada")
    transition_waiting_room(
        db,
        entry,
        data.status,
        reason=data.reason,
        actor_role=current_user.role,
    )
    db.commit()
    db.refresh(entry)
    audit(db, clinic_id=current_user.clinic_id, user_id=current_user.id, action="UPDATE", resource="waiting_room_entry", resource_id=entry.id, details={"status": data.status.value, "reason": data.reason}, ip_address=request.client.host if request else None)
    entry = _entry_query(db, current_user.clinic_id).filter(WaitingRoomEntry.id == entry.id).first()
    return _entry_response(entry)
