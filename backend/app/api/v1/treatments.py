from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import CurrentUser, get_current_user, require_permission
from app.models.treatment import Treatment
from app.models.appointment import Appointment
from app.schemas.treatment import TreatmentCreate, TreatmentUpdate, TreatmentResponse
from app.services.audit import audit

router = APIRouter()


@router.get("/", response_model=List[TreatmentResponse])
def list_treatments(
    response: Response,
    skip: int = 0,
    limit: int = 100,
    appointment_id: Optional[int] = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Treatment).filter(Treatment.clinic_id == current_user.clinic_id)
    if appointment_id:
        query = query.filter(Treatment.appointment_id == appointment_id)
    total = query.count()
    treatments = query.order_by(Treatment.created_at.desc()).offset(skip).limit(limit).all()
    response.headers["X-Total-Count"] = str(total)
    return treatments


@router.post("/", response_model=TreatmentResponse)
def create_treatment(
    data: TreatmentCreate,
    current_user: CurrentUser = Depends(require_permission("treatment:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    appointment = db.query(Appointment).filter(
        Appointment.id == data.appointment_id,
        Appointment.clinic_id == current_user.clinic_id,
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    treatment = Treatment(clinic_id=current_user.clinic_id, **data.model_dump())
    db.add(treatment)
    db.commit()
    db.refresh(treatment)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="CREATE",
        resource="treatment",
        resource_id=treatment.id,
        details={"appointment_id": treatment.appointment_id, "diagnosis": treatment.diagnosis},
        ip_address=request.client.host if request else None,
    )
    return treatment


@router.get("/{treatment_id}", response_model=TreatmentResponse)
def get_treatment(
    treatment_id: int,
    current_user: CurrentUser = Depends(require_permission("treatment:read")),
    db: Session = Depends(get_db),
):
    t = db.query(Treatment).filter(
        Treatment.id == treatment_id,
        Treatment.clinic_id == current_user.clinic_id,
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tratamento não encontrado")
    return t


@router.patch("/{treatment_id}", response_model=TreatmentResponse)
def update_treatment(
    treatment_id: int,
    data: TreatmentUpdate,
    current_user: CurrentUser = Depends(require_permission("treatment:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    t = db.query(Treatment).filter(
        Treatment.id == treatment_id,
        Treatment.clinic_id == current_user.clinic_id,
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tratamento não encontrado")
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(t, key, value)
    db.commit()
    db.refresh(t)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="UPDATE",
        resource="treatment",
        resource_id=t.id,
        details=updates,
        ip_address=request.client.host if request else None,
    )
    return t


@router.delete("/{treatment_id}")
def delete_treatment(
    treatment_id: int,
    current_user: CurrentUser = Depends(require_permission("treatment:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    t = db.query(Treatment).filter(
        Treatment.id == treatment_id,
        Treatment.clinic_id == current_user.clinic_id,
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tratamento não encontrado")
    diag = t.diagnosis
    db.delete(t)
    db.commit()
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="DELETE",
        resource="treatment",
        resource_id=treatment_id,
        details={"diagnosis": diag},
        ip_address=request.client.host if request else None,
    )
    return {"ok": True}
