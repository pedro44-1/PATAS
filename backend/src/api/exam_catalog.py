from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload

from src.core.database import get_db
from src.core.deps import CurrentUser, require_permission
from src.models.clinical_exam import ClinicalExamFinding, ClinicalExamSystem
from src.schemas.exam_catalog import (
    ExamCatalogResponse,
    ExamFindingCreate,
    ExamFindingResponse,
    ExamFindingUpdate,
    ExamSystemCreate,
    ExamSystemResponse,
    ExamSystemUpdate,
)
from src.services.audit import audit
from src.services.clinical_catalog import ensure_clinic_defaults

router = APIRouter()


def _system_or_404(db: Session, clinic_id: int, system_id: int) -> ClinicalExamSystem:
    system = db.query(ClinicalExamSystem).filter(
        ClinicalExamSystem.id == system_id,
        ClinicalExamSystem.clinic_id == clinic_id,
    ).first()
    if not system:
        raise HTTPException(status_code=404, detail="Sistema de exame não encontrado")
    return system


def _finding_or_404(db: Session, clinic_id: int, finding_id: int) -> ClinicalExamFinding:
    finding = db.query(ClinicalExamFinding).filter(
        ClinicalExamFinding.id == finding_id,
        ClinicalExamFinding.clinic_id == clinic_id,
    ).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Achado clínico não encontrado")
    return finding


def _catalog_response(db: Session, clinic_id: int) -> ExamCatalogResponse:
    systems = db.query(ClinicalExamSystem).options(
        joinedload(ClinicalExamSystem.findings),
    ).filter(
        ClinicalExamSystem.clinic_id == clinic_id,
    ).order_by(ClinicalExamSystem.sort_order, ClinicalExamSystem.name).all()
    return ExamCatalogResponse(systems=[
        ExamSystemResponse(
            id=system.id,
            clinic_id=system.clinic_id,
            name=system.name,
            sort_order=system.sort_order,
            active=bool(system.active),
            created_at=system.created_at,
            findings=[
                ExamFindingResponse(
                    id=finding.id,
                    clinic_id=finding.clinic_id,
                    system_id=finding.system_id,
                    name=finding.name,
                    sort_order=finding.sort_order,
                    active=bool(finding.active),
                    created_at=finding.created_at,
                )
                for finding in sorted(system.findings, key=lambda item: (item.sort_order, item.name))
            ],
        )
        for system in systems
    ])


@router.get("/", response_model=ExamCatalogResponse)
def get_exam_catalog(
    current_user: CurrentUser = Depends(require_permission("exam_catalog:read")),
    db: Session = Depends(get_db),
):
    ensure_clinic_defaults(db, current_user.clinic_id)
    return _catalog_response(db, current_user.clinic_id)


@router.post("/systems", response_model=ExamSystemResponse)
def create_exam_system(
    data: ExamSystemCreate,
    current_user: CurrentUser = Depends(require_permission("exam_catalog:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    if db.query(ClinicalExamSystem).filter(
        ClinicalExamSystem.clinic_id == current_user.clinic_id,
        ClinicalExamSystem.name.ilike(data.name),
    ).first():
        raise HTTPException(status_code=409, detail="Já existe este sistema no catálogo")
    system = ClinicalExamSystem(clinic_id=current_user.clinic_id, name=data.name, sort_order=data.sort_order, active=1)
    db.add(system)
    db.commit()
    db.refresh(system)
    audit(db, clinic_id=current_user.clinic_id, user_id=current_user.id, action="CREATE", resource="exam_system", resource_id=system.id, details={"name": system.name}, ip_address=request.client.host if request else None)
    catalog = _catalog_response(db, current_user.clinic_id)
    return next(item for item in catalog.systems if item.id == system.id)


@router.patch("/systems/{system_id}", response_model=ExamSystemResponse)
def update_exam_system(
    system_id: int,
    data: ExamSystemUpdate,
    current_user: CurrentUser = Depends(require_permission("exam_catalog:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    system = _system_or_404(db, current_user.clinic_id, system_id)
    updates = data.model_dump(exclude_unset=True)
    if "name" in updates and db.query(ClinicalExamSystem).filter(
        ClinicalExamSystem.clinic_id == current_user.clinic_id,
        ClinicalExamSystem.name.ilike(updates["name"]),
        ClinicalExamSystem.id != system_id,
    ).first():
        raise HTTPException(status_code=409, detail="Já existe este sistema no catálogo")
    for key, value in updates.items():
        setattr(system, key, int(value) if key == "active" else value)
    db.commit()
    audit(db, clinic_id=current_user.clinic_id, user_id=current_user.id, action="UPDATE", resource="exam_system", resource_id=system.id, details=updates, ip_address=request.client.host if request else None)
    catalog = _catalog_response(db, current_user.clinic_id)
    return next(item for item in catalog.systems if item.id == system_id)


@router.post("/systems/{system_id}/findings", response_model=ExamFindingResponse)
def create_exam_finding(
    system_id: int,
    data: ExamFindingCreate,
    current_user: CurrentUser = Depends(require_permission("exam_catalog:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    system = _system_or_404(db, current_user.clinic_id, system_id)
    if db.query(ClinicalExamFinding).filter(
        ClinicalExamFinding.system_id == system.id,
        ClinicalExamFinding.name.ilike(data.name),
    ).first():
        raise HTTPException(status_code=409, detail="Já existe este achado no sistema")
    finding = ClinicalExamFinding(clinic_id=current_user.clinic_id, system_id=system.id, name=data.name, sort_order=data.sort_order, active=1)
    db.add(finding)
    db.commit()
    db.refresh(finding)
    audit(db, clinic_id=current_user.clinic_id, user_id=current_user.id, action="CREATE", resource="exam_finding", resource_id=finding.id, details={"system_id": system.id, "name": finding.name}, ip_address=request.client.host if request else None)
    return finding


@router.patch("/findings/{finding_id}", response_model=ExamFindingResponse)
def update_exam_finding(
    finding_id: int,
    data: ExamFindingUpdate,
    current_user: CurrentUser = Depends(require_permission("exam_catalog:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    finding = _finding_or_404(db, current_user.clinic_id, finding_id)
    updates = data.model_dump(exclude_unset=True)
    if "name" in updates and db.query(ClinicalExamFinding).filter(
        ClinicalExamFinding.system_id == finding.system_id,
        ClinicalExamFinding.name.ilike(updates["name"]),
        ClinicalExamFinding.id != finding_id,
    ).first():
        raise HTTPException(status_code=409, detail="Já existe este achado no sistema")
    for key, value in updates.items():
        setattr(finding, key, int(value) if key == "active" else value)
    db.commit()
    db.refresh(finding)
    audit(db, clinic_id=current_user.clinic_id, user_id=current_user.id, action="UPDATE", resource="exam_finding", resource_id=finding.id, details=updates, ip_address=request.client.host if request else None)
    return finding
