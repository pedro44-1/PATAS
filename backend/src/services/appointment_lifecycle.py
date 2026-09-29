from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.core.timezones import utc_naive
from src.models.appointment import Appointment, AppointmentStatus
from src.models.user import UserRole
from src.models.waiting_room import WaitingRoomEntry, WaitingRoomStatus

APPOINTMENT_TRANSITIONS = {
    AppointmentStatus.SCHEDULED: {
        AppointmentStatus.IN_PROGRESS,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.IN_PROGRESS: {AppointmentStatus.COMPLETED},
    AppointmentStatus.COMPLETED: set(),
    AppointmentStatus.CANCELLED: set(),
    AppointmentStatus.NO_SHOW: set(),
}

WAITING_ROOM_TRANSITIONS = {
    WaitingRoomStatus.WAITING: {
        WaitingRoomStatus.CALLED,
        WaitingRoomStatus.CANCELLED,
        WaitingRoomStatus.NO_SHOW,
    },
    WaitingRoomStatus.CALLED: {
        WaitingRoomStatus.IN_PROGRESS,
        WaitingRoomStatus.CANCELLED,
        WaitingRoomStatus.NO_SHOW,
    },
    WaitingRoomStatus.IN_PROGRESS: {WaitingRoomStatus.COMPLETED},
    WaitingRoomStatus.COMPLETED: set(),
    WaitingRoomStatus.CANCELLED: set(),
    WaitingRoomStatus.NO_SHOW: set(),
}


def ensure_no_appointment_conflict(
    db: Session,
    clinic_id: int,
    vet_id: int,
    scheduled_at: datetime,
    duration_min: int,
    exclude_id: int | None = None,
) -> None:
    start = utc_naive(scheduled_at)
    end = start + timedelta(minutes=duration_min)
    query = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.vet_id == vet_id,
        Appointment.status.notin_([AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]),
    )
    if exclude_id is not None:
        query = query.filter(Appointment.id != exclude_id)
    for existing in query.all():
        existing_start = utc_naive(existing.scheduled_at)
        existing_end = existing_start + timedelta(minutes=existing.duration_min or 30)
        if start < existing_end and end > existing_start:
            raise HTTPException(status_code=409, detail="O veterinário já tem uma consulta nesse horário")


def _role_value(role: UserRole | str) -> str:
    return role.value if isinstance(role, UserRole) else role


def _require_clinical_role(role: UserRole | str) -> None:
    if _role_value(role) not in {UserRole.VET.value, UserRole.ADMIN.value}:
        raise HTTPException(status_code=403, detail="Apenas veterinários podem iniciar ou concluir atendimentos")


def _validated_reason(status: AppointmentStatus | WaitingRoomStatus, reason: str | None) -> str | None:
    normalized = (reason or "").strip() or None
    if status in {AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW, WaitingRoomStatus.CANCELLED, WaitingRoomStatus.NO_SHOW} and not normalized:
        raise HTTPException(status_code=422, detail="O motivo é obrigatório para cancelar ou marcar falta")
    return normalized


def transition_appointment(
    db: Session,
    appointment: Appointment,
    next_status: AppointmentStatus,
    *,
    reason: str | None,
    actor_role: UserRole | str,
    sync_waiting_room: bool = True,
) -> None:
    current_status = AppointmentStatus(appointment.status)
    if next_status not in APPOINTMENT_TRANSITIONS[current_status]:
        raise HTTPException(status_code=409, detail="Transição de estado inválida para esta consulta")
    if next_status in {AppointmentStatus.IN_PROGRESS, AppointmentStatus.COMPLETED}:
        _require_clinical_role(actor_role)
    normalized_reason = _validated_reason(next_status, reason)

    appointment.status = next_status
    appointment.status_reason = normalized_reason
    if not sync_waiting_room or appointment.waiting_room_entry is None:
        return

    entry = appointment.waiting_room_entry
    now = datetime.now(UTC).replace(tzinfo=None)
    target_status = WaitingRoomStatus(next_status.value)
    entry.status = target_status.value
    entry.status_reason = normalized_reason
    if target_status == WaitingRoomStatus.IN_PROGRESS:
        entry.started_at = entry.started_at or now
    elif target_status in {
        WaitingRoomStatus.COMPLETED,
        WaitingRoomStatus.CANCELLED,
        WaitingRoomStatus.NO_SHOW,
    }:
        entry.completed_at = entry.completed_at or now
    db.flush()


def transition_waiting_room(
    db: Session,
    entry: WaitingRoomEntry,
    next_status: WaitingRoomStatus,
    *,
    reason: str | None,
    actor_role: UserRole | str,
) -> None:
    current_status = WaitingRoomStatus(entry.status)
    if next_status not in WAITING_ROOM_TRANSITIONS[current_status]:
        raise HTTPException(status_code=409, detail="Transição de estado inválida para esta entrada")
    if next_status in {WaitingRoomStatus.IN_PROGRESS, WaitingRoomStatus.COMPLETED}:
        _require_clinical_role(actor_role)
    normalized_reason = _validated_reason(next_status, reason)

    now = datetime.now(UTC).replace(tzinfo=None)
    entry.status = next_status.value
    entry.status_reason = normalized_reason
    if next_status == WaitingRoomStatus.CALLED:
        entry.called_at = entry.called_at or now
    elif next_status == WaitingRoomStatus.IN_PROGRESS:
        entry.started_at = entry.started_at or now
        transition_appointment(
            db,
            entry.appointment,
            AppointmentStatus.IN_PROGRESS,
            reason=None,
            actor_role=actor_role,
            sync_waiting_room=False,
        )
    elif next_status in {
        WaitingRoomStatus.COMPLETED,
        WaitingRoomStatus.CANCELLED,
        WaitingRoomStatus.NO_SHOW,
    }:
        entry.completed_at = entry.completed_at or now
        transition_appointment(
            db,
            entry.appointment,
            AppointmentStatus(next_status.value),
            reason=normalized_reason,
            actor_role=actor_role,
            sync_waiting_room=False,
        )
    db.flush()
