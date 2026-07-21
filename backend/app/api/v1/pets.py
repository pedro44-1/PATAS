from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import CurrentUser, get_current_user
from app.models.pet import Pet
from app.models.owner import Owner
from app.schemas.pet import PetCreate, PetUpdate, PetResponse
from app.services.audit import audit

router = APIRouter()


@router.get("/", response_model=List[PetResponse])
def list_pets(
    response: Response,
    skip: int = 0,
    limit: int = 100,
    q: Optional[str] = None,
    owner_id: Optional[int] = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Pet).filter(Pet.clinic_id == current_user.clinic_id)
    if owner_id:
        query = query.filter(Pet.owner_id == owner_id)
    if q:
        like = f"%{q}%"
        query = query.filter(Pet.name.ilike(like))
    total = query.count()
    pets = query.order_by(Pet.created_at.desc()).offset(skip).limit(limit).all()
    response.headers["X-Total-Count"] = str(total)
    return pets


@router.post("/", response_model=PetResponse)
def create_pet(
    data: PetCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    owner = db.query(Owner).filter(
        Owner.id == data.owner_id, Owner.clinic_id == current_user.clinic_id
    ).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Dono não encontrado")

    pet = Pet(clinic_id=current_user.clinic_id, **data.model_dump())
    db.add(pet)
    db.commit()
    db.refresh(pet)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="CREATE",
        resource="pet",
        resource_id=pet.id,
        details={"name": pet.name, "owner_id": pet.owner_id},
        ip_address=request.client.host if request else None,
    )
    return pet


@router.get("/{pet_id}", response_model=PetResponse)
def get_pet(
    pet_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet = db.query(Pet).filter(
        Pet.id == pet_id, Pet.clinic_id == current_user.clinic_id
    ).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    return pet


@router.patch("/{pet_id}", response_model=PetResponse)
def update_pet(
    pet_id: int,
    data: PetUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    pet = db.query(Pet).filter(
        Pet.id == pet_id, Pet.clinic_id == current_user.clinic_id
    ).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Animal não encontrado")

    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(pet, key, value)
    db.commit()
    db.refresh(pet)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="UPDATE",
        resource="pet",
        resource_id=pet.id,
        details=updates,
        ip_address=request.client.host if request else None,
    )
    return pet


@router.delete("/{pet_id}")
def delete_pet(
    pet_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    pet = db.query(Pet).filter(
        Pet.id == pet_id, Pet.clinic_id == current_user.clinic_id
    ).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    pet_name = pet.name
    db.delete(pet)
    db.commit()
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="DELETE",
        resource="pet",
        resource_id=pet_id,
        details={"name": pet_name},
        ip_address=request.client.host if request else None,
    )
    return {"ok": True}
