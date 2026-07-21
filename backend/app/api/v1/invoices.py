from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import CurrentUser, get_current_user, require_permission
from app.models.invoice import Invoice
from app.models.owner import Owner
from app.models.appointment import Appointment
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceResponse
from app.services.audit import audit

router = APIRouter()


@router.get("/", response_model=List[InvoiceResponse])
def list_invoices(
    response: Response,
    skip: int = 0,
    limit: int = 100,
    owner_id: Optional[int] = None,
    status: Optional[str] = None,
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
        Owner.id == data.owner_id, Owner.clinic_id == current_user.clinic_id
    ).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Dono não encontrado")

    if data.appointment_id:
        appointment = db.query(Appointment).filter(
            Appointment.id == data.appointment_id, Appointment.clinic_id == current_user.clinic_id
        ).first()
        if not appointment:
            raise HTTPException(status_code=404, detail="Consulta não encontrada")

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


@router.delete("/{invoice_id}")
def delete_invoice(
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
    amt = inv.amount
    db.delete(inv)
    db.commit()
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="DELETE",
        resource="invoice",
        resource_id=invoice_id,
        details={"amount": amt},
        ip_address=request.client.host if request else None,
    )
    return {"ok": True}
