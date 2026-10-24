
import httpx
from sqlalchemy.orm import Session

from src.core.timezones import utc_now
from src.models.invoice import Invoice, InvoiceDocumentType, InvoiceStatus
from src.services.audit import audit
from src.services.billing import BillingAdapter, get_billing_adapter, is_paid_provider_state


def reconcile_invoice(
    db: Session,
    invoice: Invoice,
    *,
    user_id: int | None = None,
    adapter: BillingAdapter | None = None,
) -> str | None:
    if not invoice.external_reference:
        return None
    adapter = adapter or get_billing_adapter()
    external_status = adapter.get_status(invoice.external_reference)
    now = utc_now()
    invoice.provider_status = external_status
    invoice.last_sync_at = now
    became_paid = invoice.status == InvoiceStatus.SENT and is_paid_provider_state(external_status)
    if became_paid:
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = now
    db.commit()
    if became_paid:
        audit(
            db,
            clinic_id=invoice.clinic_id,
            user_id=user_id,
            action="RECONCILE",
            resource="invoice",
            resource_id=invoice.id,
            details={"status": InvoiceStatus.PAID.value, "provider_status": external_status},
        )
    return external_status


def pending_payment_invoices(db: Session, limit: int = 200) -> list[Invoice]:
    return (
        db.query(Invoice)
        .filter(
            Invoice.status == InvoiceStatus.SENT,
            Invoice.document_type == InvoiceDocumentType.INVOICE,
            Invoice.external_reference.isnot(None),
        )
        .order_by(Invoice.last_sync_at.asc().nullsfirst(), Invoice.id.asc())
        .limit(limit)
        .all()
    )


def reconcile_pending_invoices(db: Session, adapter: BillingAdapter | None = None) -> dict[str, int]:
    adapter = adapter or get_billing_adapter()
    result = {"checked": 0, "paid": 0, "failed": 0}
    for invoice in pending_payment_invoices(db):
        result["checked"] += 1
        try:
            reconcile_invoice(db, invoice, adapter=adapter)
        except (httpx.HTTPError, KeyError, ValueError):
            db.rollback()
            result["failed"] += 1
            continue
        if invoice.status == InvoiceStatus.PAID:
            result["paid"] += 1
    return result
