from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel

from src.core.database import get_db
from src.core.deps import CurrentUser, get_current_user
from src.models.appointment import Appointment, AppointmentStatus
from src.models.owner import Owner
from src.models.pet import Pet

router = APIRouter()


class StatusCount(BaseModel):
    scheduled: int = 0
    completed: int = 0
    cancelled: int = 0
    no_show: int = 0


class DashboardResponse(BaseModel):
    today_appointments_total: int
    today_appointments_by_status: StatusCount
    upcoming_appointments: list[dict]
    total_owners: int
    total_pets: int


@router.get("/", response_model=DashboardResponse)
def dashboard(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    clinic_id = current_user.clinic_id
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    today_appts = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.scheduled_at >= today_start,
        Appointment.scheduled_at < today_end,
    ).all()

    status_count = StatusCount()
    for a in today_appts:
        if a.status == AppointmentStatus.SCHEDULED:
            status_count.scheduled += 1
        elif a.status == AppointmentStatus.COMPLETED:
            status_count.completed += 1
        elif a.status == AppointmentStatus.CANCELLED:
            status_count.cancelled += 1
        elif a.status == AppointmentStatus.NO_SHOW:
            status_count.no_show += 1

    upcoming = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.scheduled_at >= now,
        Appointment.status == AppointmentStatus.SCHEDULED,
    ).order_by(Appointment.scheduled_at).limit(10).all()

    total_owners = db.query(Owner).filter(Owner.clinic_id == clinic_id).count()
    total_pets = db.query(Pet).filter(Pet.clinic_id == clinic_id).count()

    return DashboardResponse(
        today_appointments_total=len(today_appts),
        today_appointments_by_status=status_count,
        upcoming_appointments=[
            {
                "id": a.id,
                "pet_id": a.pet_id,
                "vet_id": a.vet_id,
                "scheduled_at": a.scheduled_at.isoformat(),
                "reason": a.reason,
                "status": a.status.value,
            }
            for a in upcoming
        ],
        total_owners=total_owners,
        total_pets=total_pets,
    )
