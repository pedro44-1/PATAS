
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.deps import CurrentUser, get_current_user, require_permission
from src.models.appointment import Appointment
from src.models.treatment import Treatment
from src.models.user import User, UserRole
from src.schemas.treatment import TreatmentCreate, TreatmentResponse, TreatmentUpdate
from src.services.audit import audit

router = APIRouter()


def _validate_referring_vet(db: Session, clinic_id: int, vet_id: int | None) -> None:
    if vet_id is None:
        return
    vet = db.query(User).filter(
        User.id == vet_id,
        User.clinic_id == clinic_id,
        User.role.in_([UserRole.VET, UserRole.ADMIN]),
    ).first()
    if not vet:
        raise HTTPException(status_code=422, detail="O veterinário referenciador não pertence à clínica")


@router.get("/", response_model=list[TreatmentResponse])
def list_treatments(
    response: Response,
    skip: int = 0,
    limit: int = 100,
    appointment_id: int | None = None,
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
    _validate_referring_vet(db, current_user.clinic_id, data.referring_vet_id)

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
    _validate_referring_vet(db, current_user.clinic_id, updates.get("referring_vet_id", t.referring_vet_id))
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
    raise HTTPException(
        status_code=405,
        detail="Tratamentos clínicos não podem ser eliminados; efetue uma correção auditada",
    )
