from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import CurrentUser, get_current_user
from app.core.safe_update import safe_update
from app.models.owner import Owner
from app.schemas.owner import OwnerCreate, OwnerUpdate, OwnerResponse
from app.services.audit import audit

router = APIRouter()

OWNER_FIELDS = {"name", "phone", "email", "address", "notes"}


@router.get("/", response_model=List[OwnerResponse])
def list_owners(
    response: Response,
    skip: int = 0,
    limit: int = 100,
    q: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Owner).filter(Owner.clinic_id == current_user.clinic_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Owner.name.ilike(like)) | (Owner.phone.ilike(like)) | (Owner.email.ilike(like))
        )
    total = query.count()
    owners = query.order_by(Owner.created_at.desc()).offset(skip).limit(limit).all()
    response.headers["X-Total-Count"] = str(total)
    return owners


@router.post("/", response_model=OwnerResponse)
def create_owner(
    data: OwnerCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    owner = Owner(clinic_id=current_user.clinic_id, **data.model_dump())
    db.add(owner)
    db.commit()
    db.refresh(owner)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="CREATE",
        resource="owner",
        resource_id=owner.id,
        details={"name": owner.name},
        ip_address=request.client.host if request else None,
    )
    return owner


@router.get("/{owner_id}", response_model=OwnerResponse)
def get_owner(
    owner_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owner = db.query(Owner).filter(
        Owner.id == owner_id, Owner.clinic_id == current_user.clinic_id
    ).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Dono não encontrado")
    return owner


@router.patch("/{owner_id}", response_model=OwnerResponse)
def update_owner(
    owner_id: int,
    data: OwnerUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    owner = db.query(Owner).filter(
        Owner.id == owner_id, Owner.clinic_id == current_user.clinic_id
    ).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Dono não encontrado")
    updates = data.model_dump(exclude_unset=True)
    safe_update(owner, updates, OWNER_FIELDS)
    db.commit()
    db.refresh(owner)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="UPDATE",
        resource="owner",
        resource_id=owner.id,
        details=updates,
        ip_address=request.client.host if request else None,
    )
    return owner


@router.delete("/{owner_id}")
def delete_owner(
    owner_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    owner = db.query(Owner).filter(
        Owner.id == owner_id, Owner.clinic_id == current_user.clinic_id
    ).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Dono não encontrado")
    owner_name = owner.name
    db.delete(owner)
    db.commit()
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="DELETE",
        resource="owner",
        resource_id=owner_id,
        details={"name": owner_name},
        ip_address=request.client.host if request else None,
    )
    return {"ok": True}
