from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.deps import CurrentUser, get_current_user, require_permission
from src.core.safe_update import safe_update
from src.models.clinic import Clinic
from src.schemas.clinic import ClinicResponse, ClinicUpdate
from src.services.audit import audit

router = APIRouter()
CLINIC_FIELDS = {"name", "address", "phone", "email", "nif", "billing_store_external_id"}


@router.get("/me", response_model=ClinicResponse)
def get_clinic(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    clinic = db.query(Clinic).filter(Clinic.id == current_user.clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clínica não encontrada")
    return clinic


@router.patch("/me", response_model=ClinicResponse)
def update_clinic(
    data: ClinicUpdate,
    current_user: CurrentUser = Depends(require_permission("user:manage")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    clinic = db.query(Clinic).filter(Clinic.id == current_user.clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clínica não encontrada")
    updates = data.model_dump(exclude_unset=True)
    safe_update(clinic, updates, CLINIC_FIELDS)
    db.commit()
    db.refresh(clinic)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="UPDATE",
        resource="clinic",
        resource_id=clinic.id,
        details={"fields": sorted(updates)},
        ip_address=request.client.host if request else None,
    )
    return clinic
