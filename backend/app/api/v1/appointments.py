from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.deps import CurrentUser, get_current_user
from app.models.appointment import Appointment, AppointmentStatus
from app.models.pet import Pet
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from app.services.audit import audit

router = APIRouter()


@router.get("/", response_model=List[AppointmentResponse])
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
        try:
            target = datetime.fromisoformat(date.replace("Z", "+00:00"))
            query = query.filter(
                Appointment.scheduled_at >= target.replace(hour=0, minute=0, second=0),
                Appointment.scheduled_at < target.replace(hour=23, minute=59, second=59),
            )
        except ValueError:
            pass
    return query.order_by(Appointment.scheduled_at).offset(skip).limit(limit).all()


@router.post("/", response_model=AppointmentResponse)
def create_appointment(
    data: AppointmentCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    pet = db.query(Pet).filter(
        Pet.id == data.pet_id,
        Pet.clinic_id == current_user.clinic_id,
    ).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Animal não encontrado")

    appt_data = data.model_dump()
    appt_data["owner_id"] = pet.owner_id
    appt = Appointment(clinic_id=current_user.clinic_id, **appt_data)
    db.add(appt)
    db.commit()
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
    for key, value in updates.items():
        setattr(appt, key, value)
    db.commit()
    db.refresh(appt)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="UPDATE",
        resource="appointment",
        resource_id=appt.id,
        details=updates,
        ip_address=request.client.host if request else None,
    )
    return appt


@router.delete("/{appointment_id}")
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
    appt_reason = appt.reason
    db.delete(appt)
    db.commit()
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="DELETE",
        resource="appointment",
        resource_id=appointment_id,
        details={"reason": appt_reason},
        ip_address=request.client.host if request else None,
    )
    return {"ok": True}
