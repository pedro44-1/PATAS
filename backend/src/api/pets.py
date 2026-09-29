from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session, joinedload

from src.core.database import get_db
from src.core.deps import CurrentUser, get_current_user, require_permission
from src.models.appointment import Appointment
from src.models.clinical_exam import ClinicalExamFinding, ClinicalExamObservation
from src.models.medication import Medication
from src.models.owner import Owner
from src.models.pet import Pet
from src.models.vaccination import Vaccination
from src.schemas.history import PetHistoryResponse
from src.schemas.pet import PetCreate, PetResponse, PetUpdate
from src.services.audit import audit

router = APIRouter()


@router.get("/{pet_id}/history", response_model=PetHistoryResponse)
def get_pet_history(
    pet_id: int,
    current_user: CurrentUser = Depends(require_permission("clinical:read")),
    db: Session = Depends(get_db),
):
    pet = db.query(Pet).filter(
        Pet.id == pet_id,
        Pet.clinic_id == current_user.clinic_id,
    ).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    appointments = db.query(Appointment).options(
        joinedload(Appointment.treatment),
        joinedload(Appointment.service_type),
        joinedload(Appointment.exam_observations).joinedload(ClinicalExamObservation.finding).joinedload(ClinicalExamFinding.system),
    ).filter(
        Appointment.pet_id == pet_id,
        Appointment.clinic_id == current_user.clinic_id,
    ).order_by(Appointment.scheduled_at.desc()).all()
    vaccinations = db.query(Vaccination).options(
        joinedload(Vaccination.vet),
    ).filter(
        Vaccination.pet_id == pet_id,
        Vaccination.clinic_id == current_user.clinic_id,
    ).order_by(Vaccination.administered_at.desc()).all()
    medications = db.query(Medication).options(
        joinedload(Medication.vet),
    ).filter(
        Medication.pet_id == pet_id,
        Medication.clinic_id == current_user.clinic_id,
    ).order_by(Medication.start_date.desc(), Medication.created_at.desc()).all()
    return PetHistoryResponse(
        pet_id=pet_id,
        appointments=[
            {
                "id": appointment.id,
                "scheduled_at": appointment.scheduled_at,
                "vet_id": appointment.vet_id,
                "reason": appointment.reason,
                "status": appointment.status,
                "status_reason": appointment.status_reason,
                "weight": appointment.weight,
                "notes": appointment.notes,
                "treatment": appointment.treatment,
                "service_type_id": appointment.service_type_id,
                "service_type_name": appointment.service_type.name if appointment.service_type else None,
                "exam_findings": [
                    {
                        "id": observation.id,
                        "appointment_id": observation.appointment_id,
                        "finding_id": observation.finding_id,
                        "finding_name": observation.finding_name,
                        "system_id": observation.finding.system_id if observation.finding else 0,
                        "system_name": observation.finding.system.name if observation.finding and observation.finding.system else "",
                        "status": observation.status,
                        "note": observation.note,
                    }
                    for observation in appointment.exam_observations
                ],
            }
            for appointment in appointments
        ],
        vaccinations=[
            {
                "id": vaccination.id,
                "clinic_id": vaccination.clinic_id,
                "pet_id": vaccination.pet_id,
                "appointment_id": vaccination.appointment_id,
                "vet_id": vaccination.vet_id,
                "vet_name": vaccination.vet.name if vaccination.vet else None,
                "name": vaccination.name,
                "administered_at": vaccination.administered_at,
                "dose": vaccination.dose,
                "lot_number": vaccination.lot_number,
                "expires_at": vaccination.expires_at,
                "next_due_at": vaccination.next_due_at,
                "notes": vaccination.notes,
                "status": vaccination.status,
                "void_reason": vaccination.void_reason,
                "voided_at": vaccination.voided_at,
                "created_at": vaccination.created_at,
                "updated_at": vaccination.updated_at,
            }
            for vaccination in vaccinations
        ],
        medications=[
            {
                "id": medication.id,
                "clinic_id": medication.clinic_id,
                "pet_id": medication.pet_id,
                "appointment_id": medication.appointment_id,
                "vet_id": medication.vet_id,
                "vet_name": medication.vet.name if medication.vet else None,
                "name": medication.name,
                "dosage": medication.dosage,
                "frequency": medication.frequency,
                "route": medication.route,
                "start_date": medication.start_date,
                "end_date": medication.end_date,
                "instructions": medication.instructions,
                "notes": medication.notes,
                "status": medication.status,
                "void_reason": medication.void_reason,
                "voided_at": medication.voided_at,
                "created_at": medication.created_at,
                "updated_at": medication.updated_at,
            }
            for medication in medications
        ],
    )


@router.get("/", response_model=list[PetResponse])
def list_pets(
    response: Response,
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
    owner_id: int | None = None,
    include_archived: bool = False,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Pet).filter(Pet.clinic_id == current_user.clinic_id)
    if not include_archived:
        query = query.filter(Pet.archived_at.is_(None))
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
        Owner.id == data.owner_id,
        Owner.clinic_id == current_user.clinic_id,
        Owner.archived_at.is_(None),
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
    if pet.archived_at is not None:
        raise HTTPException(status_code=409, detail="Um animal arquivado não pode ser alterado")

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
    if pet.archived_at is not None:
        return {"ok": True, "archived_at": pet.archived_at}
    archived_at = datetime.now(UTC)
    pet.archived_at = archived_at
    pet.archived_by_user_id = current_user.id
    db.commit()
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="ARCHIVE",
        resource="pet",
        resource_id=pet_id,
        details={"name": pet.name},
        ip_address=request.client.host if request else None,
    )
    return {"ok": True, "archived_at": archived_at}
