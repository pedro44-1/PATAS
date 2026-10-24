import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.deps import CurrentUser, require_permission
from src.models.service_type import ServiceType
from src.schemas.service_type import ServiceTypeCreate, ServiceTypeResponse, ServiceTypeUpdate
from src.services.audit import audit
from src.services.clinical_catalog import ensure_clinic_defaults

router = APIRouter()


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-") or "servico"


def _get_service_type(db: Session, clinic_id: int, service_type_id: int) -> ServiceType:
    service_type = db.query(ServiceType).filter(
        ServiceType.id == service_type_id,
        ServiceType.clinic_id == clinic_id,
    ).first()
    if not service_type:
        raise HTTPException(status_code=404, detail="Tipo de serviço não encontrado")
    return service_type


@router.get("/", response_model=list[ServiceTypeResponse])
def list_service_types(
    current_user: CurrentUser = Depends(require_permission("service_type:read")),
    db: Session = Depends(get_db),
):
    ensure_clinic_defaults(db, current_user.clinic_id)
    return db.query(ServiceType).filter(
        ServiceType.clinic_id == current_user.clinic_id,
    ).order_by(ServiceType.sort_order, ServiceType.name).all()


@router.post("/", response_model=ServiceTypeResponse)
def create_service_type(
    data: ServiceTypeCreate,
    current_user: CurrentUser = Depends(require_permission("service_type:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    slug = _slugify(data.name)
    if db.query(ServiceType).filter(ServiceType.clinic_id == current_user.clinic_id, ServiceType.slug == slug).first():
        raise HTTPException(status_code=409, detail="Já existe um tipo de serviço com este nome")
    service_type = ServiceType(clinic_id=current_user.clinic_id, slug=slug, **data.model_dump())
    db.add(service_type)
    db.commit()
    db.refresh(service_type)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="CREATE",
        resource="service_type",
        resource_id=service_type.id,
        details={"name": service_type.name},
        ip_address=request.client.host if request else None,
    )
    return service_type


@router.patch("/{service_type_id}", response_model=ServiceTypeResponse)
def update_service_type(
    service_type_id: int,
    data: ServiceTypeUpdate,
    current_user: CurrentUser = Depends(require_permission("service_type:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    service_type = _get_service_type(db, current_user.clinic_id, service_type_id)
    updates = data.model_dump(exclude_unset=True)
    if "name" in updates:
        next_slug = _slugify(updates["name"])
        duplicate = db.query(ServiceType).filter(
            ServiceType.clinic_id == current_user.clinic_id,
            ServiceType.slug == next_slug,
            ServiceType.id != service_type_id,
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Já existe um tipo de serviço com este nome")
        updates["slug"] = next_slug
    for key, value in updates.items():
        setattr(service_type, key, value)
    db.commit()
    db.refresh(service_type)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="UPDATE",
        resource="service_type",
        resource_id=service_type.id,
        details=updates,
        ip_address=request.client.host if request else None,
    )
    return service_type
