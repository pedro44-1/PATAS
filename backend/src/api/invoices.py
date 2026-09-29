
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.deps import CurrentUser, get_current_user, require_permission
from src.models.appointment import Appointment
from src.models.invoice import Invoice, InvoiceStatus, InvoiceSyncStatus
from src.models.owner import Owner
from src.schemas.invoice import InvoiceCreate, InvoiceResponse, InvoiceUpdate
from src.services.audit import audit
from src.services.billing import billing_adapter

router = APIRouter()

INVOICE_TRANSITIONS = {
    InvoiceStatus.DRAFT: {InvoiceStatus.SENT, InvoiceStatus.PAID, InvoiceStatus.CANCELLED},
    InvoiceStatus.SENT: {InvoiceStatus.PAID, InvoiceStatus.CANCELLED},
    InvoiceStatus.PAID: set(),
    InvoiceStatus.CANCELLED: set(),
}


@router.get("/", response_model=list[InvoiceResponse])
def list_invoices(
    response: Response,
    skip: int = 0,
    limit: int = 100,
    owner_id: int | None = None,
    status: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Invoice).filter(Invoice.clinic_id == current_user.clinic_id)
    if owner_id:
        query = query.filter(Invoice.owner_id == owner_id)
    if status:
        query = query.filter(Invoice.status == status)
    total = query.count()
    invoices = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
    response.headers["X-Total-Count"] = str(total)
    return invoices


@router.post("/", response_model=InvoiceResponse)
def create_invoice(
    data: InvoiceCreate,
    current_user: CurrentUser = Depends(require_permission("invoice:write")),
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

    if data.appointment_id:
        appointment = db.query(Appointment).filter(
            Appointment.id == data.appointment_id, Appointment.clinic_id == current_user.clinic_id
        ).first()
        if not appointment:
            raise HTTPException(status_code=404, detail="Consulta não encontrada")
        if appointment.owner_id != data.owner_id:
            raise HTTPException(status_code=422, detail="A consulta não pertence ao dono indicado")

    invoice = Invoice(clinic_id=current_user.clinic_id, **data.model_dump())
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="CREATE",
        resource="invoice",
        resource_id=invoice.id,
        details={"amount": invoice.amount, "owner_id": invoice.owner_id},
        ip_address=request.client.host if request else None,
    )
    return invoice


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.clinic_id == current_user.clinic_id,
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    return inv


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    current_user: CurrentUser = Depends(require_permission("invoice:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    inv = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.clinic_id == current_user.clinic_id,
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    updates = data.model_dump(exclude_unset=True)
    if inv.status in {InvoiceStatus.PAID, InvoiceStatus.CANCELLED} and updates:
        raise HTTPException(status_code=409, detail="Faturas em estado terminal não podem ser alteradas")
    target_status = updates.get("status")
    if target_status and target_status != inv.status and target_status not in INVOICE_TRANSITIONS[inv.status]:
        raise HTTPException(status_code=409, detail="Transição de estado da fatura inválida")
    if inv.status != InvoiceStatus.DRAFT and set(updates) - {"status", "reason"}:
        raise HTTPException(status_code=409, detail="Apenas faturas em rascunho podem ser corrigidas")
    if target_status == InvoiceStatus.CANCELLED and not updates.get("reason"):
        raise HTTPException(status_code=422, detail="O motivo é obrigatório ao cancelar uma fatura")
    for key, value in updates.items():
        setattr(inv, key, value)
    db.commit()
    db.refresh(inv)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="UPDATE",
        resource="invoice",
        resource_id=inv.id,
        details=updates,
        ip_address=request.client.host if request else None,
    )
    return inv


@router.post("/{invoice_id}/sync", response_model=InvoiceResponse)
def sync_invoice(
    invoice_id: int,
    current_user: CurrentUser = Depends(require_permission("invoice:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    inv = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.clinic_id == current_user.clinic_id,
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    if inv.status in {InvoiceStatus.CANCELLED, InvoiceStatus.PAID}:
        raise HTTPException(status_code=409, detail="Faturas em estado terminal não podem ser sincronizadas")
    if inv.sync_status == InvoiceSyncStatus.SYNCED and inv.external_reference:
        return inv
    result = billing_adapter.create_invoice(inv)
    inv.external_reference = result.external_reference
    inv.sync_status = InvoiceSyncStatus.SYNCED
    if inv.status == InvoiceStatus.DRAFT:
        inv.status = InvoiceStatus.SENT
    db.commit()
    db.refresh(inv)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="SYNC",
        resource="invoice",
        resource_id=inv.id,
        details={"external_reference": inv.external_reference, "adapter": "mock"},
        ip_address=request.client.host if request else None,
    )
    return inv


@router.get("/{invoice_id}/sync-status")
def get_invoice_sync_status(
    invoice_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.clinic_id == current_user.clinic_id,
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    external_status = billing_adapter.get_status(inv.external_reference) if inv.external_reference else None
    return {"invoice_id": inv.id, "sync_status": inv.sync_status.value, "external_status": external_status}


@router.delete("/{invoice_id}")
def delete_invoice(
    invoice_id: int,
    current_user: CurrentUser = Depends(require_permission("invoice:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    raise HTTPException(
        status_code=405,
        detail="Faturas não podem ser eliminadas; cancele a fatura com um motivo",
    )
