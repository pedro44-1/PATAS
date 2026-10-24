import json
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session, selectinload

from src.core.database import get_db
from src.core.deps import CurrentUser, require_permission
from src.core.pagination import Limit, Skip
from src.core.timezones import stored_utc, utc_now
from src.models.appointment import Appointment, AppointmentStatus
from src.models.clinic import Clinic
from src.models.invoice import (
    Invoice,
    InvoiceLine,
    InvoiceLineKind,
    InvoiceStatus,
    InvoiceSyncStatus,
)
from src.models.owner import Owner
from src.schemas.invoice import InvoiceCreate, InvoiceResponse, InvoiceUpdate
from src.services.appointment_lifecycle import ensure_active_subject
from src.services.audit import audit
from src.services.billing import (
    build_billing_payload,
    build_billing_preview_payload,
    get_billing_adapter,
)
from src.services.billing_reconciliation import reconcile_invoice

router = APIRouter()

INVOICE_TRANSITIONS = {
    InvoiceStatus.DRAFT: {InvoiceStatus.CANCELLED},
    InvoiceStatus.SENT: {InvoiceStatus.CANCELLED},
    InvoiceStatus.PAID: set(),
    InvoiceStatus.CANCELLED: set(),
}
CENT = Decimal("0.01")
RETRYABLE_PROVIDER_STATUSES = {408, 409, 425, 429}


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _add_line(
    invoice: Invoice,
    clinic_id: int,
    description: str,
    quantity: Decimal,
    unit_price: Decimal,
    tax_rate: Decimal,
    code: str | None = None,
    vat_profile_code: str | None = None,
    kind: InvoiceLineKind = InvoiceLineKind.SERVICE,
    unit: str = "UN",
) -> None:
    subtotal = _money(quantity * unit_price)
    tax_amount = _money(subtotal * tax_rate / Decimal(100))
    invoice.lines.append(InvoiceLine(
        clinic_id=clinic_id,
        description=description,
        code=code,
        vat_profile_code=vat_profile_code,
        kind=kind,
        unit=unit,
        quantity=quantity,
        unit_price=unit_price,
        tax_rate=tax_rate,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total=subtotal + tax_amount,
    ))


def _recalculate(invoice: Invoice) -> None:
    invoice.subtotal = sum((line.subtotal for line in invoice.lines), Decimal(0))
    invoice.tax_total = sum((line.tax_amount for line in invoice.lines), Decimal(0))
    invoice.amount = _money(invoice.subtotal + invoice.tax_total)


def _find_invoice(db: Session, invoice_id: int, clinic_id: int, *, for_update: bool = False) -> Invoice:
    query = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.clinic_id == clinic_id)
    if for_update:
        query = query.with_for_update()
    invoice = query.first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    return invoice


SNAPSHOT_SOURCES = {
    "issuer_name": ("clinic", "name"),
    "issuer_nif": ("clinic", "nif"),
    "issuer_address": ("clinic", "address"),
    "issuer_phone": ("clinic", "phone"),
    "issuer_store_external_id": ("clinic", "billing_store_external_id"),
    "customer_name": ("owner", "name"),
    "customer_nif": ("owner", "nif"),
    "customer_address": ("owner", "address"),
    "customer_phone": ("owner", "phone"),
    "customer_email": ("owner", "email"),
}


def _hydrate_billing_snapshot(db: Session, invoice: Invoice, *, refresh: bool = False) -> None:
    sources = {
        "clinic": db.query(Clinic).filter(Clinic.id == invoice.clinic_id).first(),
        "owner": db.query(Owner).filter(
            Owner.id == invoice.owner_id,
            Owner.clinic_id == invoice.clinic_id,
        ).first(),
    }
    for field, (source, attribute) in SNAPSHOT_SOURCES.items():
        current = getattr(invoice, field)
        if refresh or not current:
            setattr(invoice, field, getattr(sources[source], attribute) or (None if refresh else current))
    invoice.billing_external_id = (
        invoice.billing_external_id or f"patas-{invoice.clinic_id}-invoice-{invoice.id}"
    )


def _provider_error_code(exc: httpx.HTTPStatusError) -> str | None:
    try:
        data = exc.response.json()
    except ValueError:
        return None
    detail = data.get("detail")
    if isinstance(detail, dict):
        return detail.get("code")
    return data.get("code")


def _is_definitive_rejection(status_code: int) -> bool:
    return 400 <= status_code < 500 and status_code not in RETRYABLE_PROVIDER_STATUSES


def _clear_quote(invoice: Invoice) -> None:
    invoice.quote_id = None
    invoice.quote_expires_at = None
    invoice.quote_vat_configuration_version = None
    invoice.quote_calculation_digest = None
    invoice.quote_payable = None
    invoice.quote_snapshot = None
    invoice.idempotency_key = None


@router.get("/", response_model=list[InvoiceResponse])
def list_invoices(
    response: Response,
    skip: Skip = 0,
    limit: Limit = 100,
    owner_id: int | None = None,
    appointment_id: int | None = None,
    pet_id: int | None = None,
    status: str | None = None,
    q: str | None = None,
    current_user: CurrentUser = Depends(require_permission("invoice:read")),
    db: Session = Depends(get_db),
):
    query = db.query(Invoice).options(selectinload(Invoice.lines)).filter(
        Invoice.clinic_id == current_user.clinic_id
    )
    if owner_id:
        query = query.filter(Invoice.owner_id == owner_id)
    if appointment_id:
        query = query.filter(Invoice.appointment_id == appointment_id)
    if pet_id:
        query = query.filter(Invoice.appointment.has(Appointment.pet_id == pet_id))
    if status:
        query = query.filter(Invoice.status == status)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            Invoice.document_number.ilike(like)
            | Invoice.customer_name.ilike(like)
            | Invoice.owner.has(Owner.name.ilike(like))
        )
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
    if not owner.nif:
        raise HTTPException(status_code=422, detail="O NIF do dono é obrigatório para faturação")

    if data.appointment_id:
        appointment = db.query(Appointment).filter(
            Appointment.id == data.appointment_id,
            Appointment.clinic_id == current_user.clinic_id,
        ).first()
        if not appointment:
            raise HTTPException(status_code=404, detail="Consulta não encontrada")
        if appointment.owner_id != data.owner_id:
            raise HTTPException(status_code=422, detail="A consulta não pertence ao dono indicado")
        if appointment.status in {AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW}:
            raise HTTPException(status_code=409, detail="Consultas canceladas ou faltas não podem ser faturadas")
        ensure_active_subject(appointment)
        existing = db.query(Invoice.id).filter(
            Invoice.clinic_id == current_user.clinic_id,
            Invoice.appointment_id == appointment.id,
            Invoice.status != InvoiceStatus.CANCELLED,
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Esta consulta já tem uma fatura ativa")

    clinic = db.query(Clinic).filter(Clinic.id == current_user.clinic_id).first()
    invoice = Invoice(
        clinic_id=current_user.clinic_id,
        owner_id=data.owner_id,
        appointment_id=data.appointment_id,
        amount=0,
        subtotal=0,
        tax_total=0,
        description=data.description,
        document_type=data.document_type,
        payment_method=data.payment_method,
        due_at=data.due_at,
        issuer_name=clinic.name,
        issuer_nif=clinic.nif,
        issuer_address=clinic.address,
        issuer_phone=clinic.phone,
        issuer_store_external_id=clinic.billing_store_external_id,
        customer_name=owner.name,
        customer_nif=owner.nif,
        customer_address=owner.address,
        customer_phone=owner.phone,
        customer_email=owner.email,
    )
    if data.items:
        for item in data.items:
            _add_line(
                invoice,
                current_user.clinic_id,
                item.description,
                item.quantity,
                item.unit_price,
                item.tax_rate,
                item.code,
                item.vat_profile_code,
                item.kind,
                item.unit,
            )
    else:
        _add_line(
            invoice,
            current_user.clinic_id,
            data.description or "Serviços veterinários",
            Decimal(1),
            data.amount or Decimal(0),
            Decimal(0),
        )
    _recalculate(invoice)
    db.add(invoice)
    db.flush()
    invoice.billing_external_id = f"patas-{invoice.clinic_id}-invoice-{invoice.id}"
    db.commit()
    db.refresh(invoice)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="CREATE",
        resource="invoice",
        resource_id=invoice.id,
        details={"amount": invoice.amount, "owner_id": invoice.owner_id, "lines": len(invoice.lines)},
        ip_address=request.client.host if request else None,
    )
    return invoice


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int, current_user: CurrentUser = Depends(require_permission("invoice:read")), db: Session = Depends(get_db)):
    return _find_invoice(db, invoice_id, current_user.clinic_id)


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    current_user: CurrentUser = Depends(require_permission("invoice:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    invoice = _find_invoice(db, invoice_id, current_user.clinic_id)
    updates = data.model_dump(exclude_unset=True)
    if invoice.status in {InvoiceStatus.PAID, InvoiceStatus.CANCELLED} and updates:
        raise HTTPException(status_code=409, detail="Faturas em estado terminal não podem ser alteradas")
    target_status = updates.get("status")
    if target_status == InvoiceStatus.PAID:
        raise HTTPException(
            status_code=409,
            detail="O pagamento só pode ser confirmado pelo software de faturação",
        )
    if target_status and target_status != invoice.status and target_status not in INVOICE_TRANSITIONS[invoice.status]:
        raise HTTPException(status_code=409, detail="Transição de estado da fatura inválida")
    if invoice.status != InvoiceStatus.DRAFT and set(updates) - {"status", "reason", "payment_method"}:
        raise HTTPException(status_code=409, detail="Apenas faturas em rascunho podem ser corrigidas")
    if target_status == InvoiceStatus.CANCELLED and not updates.get("reason"):
        raise HTTPException(status_code=422, detail="O motivo é obrigatório ao cancelar uma fatura")
    if target_status == InvoiceStatus.CANCELLED and invoice.external_reference:
        raise HTTPException(
            status_code=409,
            detail="O documento já foi emitido no Vendas; a anulação externa ainda não está configurada",
        )
    content_changes = set(updates) & {"amount", "description"}
    if content_changes and invoice.sync_attempts and invoice.idempotency_key:
        raise HTTPException(
            status_code=409,
            detail="Existe uma emissão pendente; repita a emissão antes de alterar a fatura",
        )
    if content_changes:
        _clear_quote(invoice)
    amount = updates.pop("amount", None)
    if amount is not None:
        if len(invoice.lines) != 1:
            raise HTTPException(status_code=409, detail="Altere os itens da fatura em vez do total")
        invoice.lines[0].unit_price = amount
        invoice.lines[0].subtotal = _money(invoice.lines[0].quantity * amount)
        invoice.lines[0].tax_amount = _money(
            invoice.lines[0].subtotal * invoice.lines[0].tax_rate / Decimal(100)
        )
        invoice.lines[0].total = invoice.lines[0].subtotal + invoice.lines[0].tax_amount
        _recalculate(invoice)
    for key, value in updates.items():
        setattr(invoice, key, value)
    db.commit()
    db.refresh(invoice)
    audit(db, clinic_id=current_user.clinic_id, user_id=current_user.id, action="UPDATE", resource="invoice", resource_id=invoice.id, details=updates, ip_address=request.client.host if request else None)
    return invoice


@router.post("/{invoice_id}/preview", response_model=InvoiceResponse)
def preview_invoice(
    invoice_id: int,
    current_user: CurrentUser = Depends(require_permission("invoice:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    invoice = _find_invoice(db, invoice_id, current_user.clinic_id, for_update=True)
    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(status_code=409, detail="Apenas rascunhos podem obter uma prévia fiscal")
    if invoice.sync_attempts > 0 and invoice.idempotency_key:
        raise HTTPException(
            status_code=409,
            detail="Existe uma emissão pendente; repita a emissão com a mesma chave antes de recalcular",
        )
    _hydrate_billing_snapshot(db, invoice, refresh=True)
    preview_key = str(uuid4())
    try:
        result = get_billing_adapter().preview_invoice(
            build_billing_preview_payload(invoice), preview_key
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        code = _provider_error_code(exc)
        if code == "VAT_PROFILE_REQUIRED":
            raise HTTPException(
                status_code=422,
                detail="Configure o perfil de IVA dos produtos ou serviços no Vendas",
            ) from exc
        raise HTTPException(
            status_code=502,
            detail="O Vendas não conseguiu calcular a prévia fiscal",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Não foi possível contactar o Vendas para calcular a prévia fiscal",
        ) from exc
    invoice.quote_id = result.quote_id
    invoice.quote_expires_at = stored_utc(result.expires_at) if result.expires_at else None
    invoice.quote_vat_configuration_version = result.vat_configuration_version
    invoice.quote_calculation_digest = result.calculation_digest
    invoice.quote_payable = result.payable
    invoice.quote_snapshot = json.dumps(result.snapshot, ensure_ascii=False)
    invoice.idempotency_key = str(uuid4())
    invoice.sync_status = InvoiceSyncStatus.PENDING
    invoice.last_sync_error = None
    db.commit()
    db.refresh(invoice)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="PREVIEW",
        resource="invoice",
        resource_id=invoice.id,
        details={"quote_id": invoice.quote_id, "sync_status": invoice.sync_status.value},
        ip_address=request.client.host if request else None,
    )
    return invoice


@router.post("/{invoice_id}/sync", response_model=InvoiceResponse)
def sync_invoice(
    invoice_id: int,
    current_user: CurrentUser = Depends(require_permission("invoice:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    invoice = _find_invoice(db, invoice_id, current_user.clinic_id, for_update=True)
    if invoice.sync_status == InvoiceSyncStatus.SYNCED and invoice.external_reference:
        return invoice
    if invoice.status in {InvoiceStatus.CANCELLED, InvoiceStatus.PAID}:
        raise HTTPException(status_code=409, detail="Faturas em estado terminal não podem ser sincronizadas")
    if not invoice.quote_id or not invoice.quote_expires_at:
        raise HTTPException(
            status_code=409,
            detail="Calcule uma prévia fiscal no Vendas antes de emitir",
        )
    expires_at = invoice.quote_expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC) and invoice.sync_attempts == 0:
        _clear_quote(invoice)
        db.commit()
        raise HTTPException(status_code=409, detail="A prévia fiscal expirou; calcule uma nova")
    _hydrate_billing_snapshot(db, invoice)
    invoice.idempotency_key = invoice.idempotency_key or str(uuid4())
    db.flush()
    try:
        adapter = get_billing_adapter()
        result = adapter.emit_invoice(build_billing_payload(invoice))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        code = _provider_error_code(exc)
        if code in {"QUOTE_NOT_FOUND", "QUOTE_EXPIRED", "QUOTE_MISMATCH", "QUOTE_STALE"}:
            _clear_quote(invoice)
            invoice.sync_status = InvoiceSyncStatus.PENDING
            invoice.last_sync_error = "A prévia fiscal mudou ou expirou"
            db.commit()
            raise HTTPException(
                status_code=409,
                detail="A prévia fiscal mudou ou expirou; calcule uma nova antes de emitir",
            ) from exc
        invoice.sync_status = InvoiceSyncStatus.FAILED
        invoice.sync_attempts += 1
        invoice.last_sync_at = utc_now()
        if _is_definitive_rejection(exc.response.status_code):
            _clear_quote(invoice)
            invoice.last_sync_error = "O software de faturação rejeitou o documento; calcule uma nova prévia"
        else:
            invoice.last_sync_error = "O software de faturação não aceitou o pedido"
        db.commit()
        raise HTTPException(status_code=502, detail=invoice.last_sync_error) from exc
    except httpx.HTTPError as exc:
        invoice.sync_status = InvoiceSyncStatus.FAILED
        invoice.sync_attempts += 1
        invoice.last_sync_at = utc_now()
        invoice.last_sync_error = "O software de faturação não aceitou o pedido"
        db.commit()
        raise HTTPException(status_code=502, detail=invoice.last_sync_error) from exc
    invoice.external_reference = result.external_reference
    invoice.document_number = result.document_number
    invoice.document_url = result.document_url
    invoice.series = result.series or invoice.series
    invoice.sync_status = InvoiceSyncStatus.SYNCED
    invoice.sync_attempts += 1
    invoice.last_sync_at = utc_now()
    invoice.last_sync_error = None
    invoice.provider_status = result.status
    invoice.provider_mode = result.mode
    invoice.issued_at = utc_now()
    if invoice.document_type.value == "FR":
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = invoice.issued_at
    elif invoice.status == InvoiceStatus.DRAFT:
        invoice.status = InvoiceStatus.SENT
    db.commit()
    db.refresh(invoice)
    audit(db, clinic_id=current_user.clinic_id, user_id=current_user.id, action="SYNC", resource="invoice", resource_id=invoice.id, details={"external_reference": invoice.external_reference, "adapter": adapter.name}, ip_address=request.client.host if request else None)
    return invoice


def _reconcile(db: Session, invoice: Invoice, user_id: int) -> str | None:
    try:
        return reconcile_invoice(db, invoice, user_id=user_id, adapter=get_billing_adapter())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Não foi possível reconciliar com o software de faturação") from exc


@router.post("/{invoice_id}/reconcile", response_model=InvoiceResponse)
def reconcile_invoice_payment(
    invoice_id: int,
    current_user: CurrentUser = Depends(require_permission("invoice:read")),
    db: Session = Depends(get_db),
):
    invoice = _find_invoice(db, invoice_id, current_user.clinic_id)
    if not invoice.external_reference:
        raise HTTPException(status_code=409, detail="A fatura ainda não foi emitida no software de faturação")
    _reconcile(db, invoice, current_user.id)
    db.refresh(invoice)
    return invoice


@router.get("/{invoice_id}/sync-status")
def get_invoice_sync_status(
    invoice_id: int,
    current_user: CurrentUser = Depends(require_permission("invoice:read")),
    db: Session = Depends(get_db),
):
    invoice = _find_invoice(db, invoice_id, current_user.clinic_id)
    external_status = _reconcile(db, invoice, current_user.id) if invoice.external_reference else None
    return {"invoice_id": invoice.id, "sync_status": invoice.sync_status.value, "external_status": external_status}


@router.delete("/{invoice_id}")
def delete_invoice(invoice_id: int, current_user: CurrentUser = Depends(require_permission("invoice:write"))):
    raise HTTPException(status_code=405, detail="Faturas não podem ser eliminadas; cancele a fatura com um motivo")
