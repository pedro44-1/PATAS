from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from typing import Protocol
from uuid import NAMESPACE_URL, uuid5

import httpx

from src.core.config import settings
from src.core.timezones import local_today
from src.models.invoice import Invoice, InvoiceDocumentType, InvoiceLine


@dataclass(frozen=True)
class BillingParty:
    external_id: str
    name: str
    tax_id: str
    country: str
    email: str | None
    phone: str | None
    address: str | None
    final_consumer: bool


@dataclass(frozen=True)
class BillingLinePayload:
    external_id: str
    code: str | None
    vat_profile_code: str
    description: str
    kind: str
    unit: str
    operation_type: str | None
    quantity: Decimal
    unit_price: Decimal
    discount_percent: Decimal


@dataclass(frozen=True)
class BillingPaymentTender:
    method: str
    amount: Decimal


@dataclass(frozen=True)
class BillingPayment:
    tenders: list[BillingPaymentTender]
    external_reference: str
    session_id: str | None


@dataclass(frozen=True)
class BillingInvoicePayload:
    idempotency_key: str
    quote_id: str
    external_id: str
    store_external_id: str
    document_type: str
    document_date: str
    due_date: str | None
    external_reference: str | None
    notes: str | None
    customer: BillingParty
    lines: list[BillingLinePayload]
    payment: BillingPayment | None

    def to_vendas_dict(self) -> dict:
        customer = asdict(self.customer)
        customer_payload = {
            "externalId": customer["external_id"],
            "name": customer["name"],
            "taxId": customer["tax_id"],
            "country": customer["country"],
            "finalConsumer": customer["final_consumer"],
        }
        for key in ("email", "phone", "address"):
            if customer[key] is not None:
                customer_payload[key] = customer[key]
        payload = {
            "quoteId": self.quote_id,
            "externalId": self.external_id,
            "storeExternalId": self.store_external_id,
            "type": self.document_type,
            "documentDate": self.document_date,
            "customer": customer_payload,
            "lines": [_line_to_vendas_dict(line) for line in self.lines],
        }
        if self.due_date is not None:
            payload["dueDate"] = self.due_date
        if self.external_reference is not None:
            payload["externalReference"] = self.external_reference
        if self.notes is not None:
            payload["notes"] = self.notes
        if self.payment:
            payment_payload = {
                "tenders": [
                    {"method": tender.method, "amount": _decimal_string(tender.amount)}
                    for tender in self.payment.tenders
                ],
                "externalReference": self.payment.external_reference,
            }
            if self.payment.session_id is not None:
                payment_payload["sessionId"] = self.payment.session_id
            payload["payment"] = payment_payload
        return payload


@dataclass(frozen=True)
class BillingSyncResult:
    external_reference: str
    status: str
    document_number: str | None = None
    series: str | None = None
    document_url: str | None = None
    mode: str | None = None


@dataclass(frozen=True)
class BillingPreviewPayload:
    external_id: str
    store_external_id: str
    document_date: str
    lines: list[BillingLinePayload]

    def to_vendas_dict(self) -> dict:
        return {
            "externalId": self.external_id,
            "storeExternalId": self.store_external_id,
            "documentDate": self.document_date,
            "lines": [_line_to_vendas_dict(line) for line in self.lines],
        }


@dataclass(frozen=True)
class BillingQuoteResult:
    quote_id: str
    expires_at: datetime
    vat_configuration_version: str
    calculation_digest: str
    payable: Decimal
    snapshot: dict


class BillingAdapter(Protocol):
    name: str

    def preview_invoice(
        self, payload: BillingPreviewPayload, idempotency_key: str
    ) -> BillingQuoteResult: ...

    def emit_invoice(self, payload: BillingInvoicePayload) -> BillingSyncResult: ...

    def get_status(self, external_reference: str) -> str: ...


def _billing_lines(invoice: Invoice) -> list[BillingLinePayload]:
    result = []
    for line in invoice.lines:
        code = line.code or _stable_line_code(line)
        result.append(BillingLinePayload(
            external_id=_stable_product_external_id(line, code),
            code=code,
            vat_profile_code=(
                line.vat_profile_code or settings.VENDAS_DEFAULT_VAT_PROFILE_CODE
            ),
            description=line.description,
            kind=line.kind.value,
            unit=line.unit,
            operation_type=settings.VENDAS_OPERATION_TYPE or None,
            quantity=line.quantity,
            unit_price=line.unit_price,
            discount_percent=Decimal(0),
        ))
    return result


def _stable_line_code(line: InvoiceLine) -> str:
    identity = f"{line.clinic_id}|{line.kind.value}|{line.description.strip().casefold()}"
    digest = sha256(identity.encode("utf-8")).hexdigest()[:16].upper()
    return f"PATAS-{line.kind.value}-{digest}"


def _stable_product_external_id(line: InvoiceLine, code: str) -> str:
    identity = f"{line.clinic_id}|{line.kind.value}|{code.strip().casefold()}"
    digest = sha256(identity.encode("utf-8")).hexdigest()[:20]
    return f"patas-product-{line.clinic_id}-{line.kind.value.lower()}-{digest}"


def build_billing_preview_payload(invoice: Invoice) -> BillingPreviewPayload:
    if not invoice.issuer_store_external_id:
        raise ValueError("A clínica precisa do identificador de loja do Vendas")
    if not invoice.lines:
        raise ValueError("A fatura precisa de pelo menos uma linha")
    if any(
        not (line.vat_profile_code or settings.VENDAS_DEFAULT_VAT_PROFILE_CODE)
        for line in invoice.lines
    ):
        raise ValueError("Configure um perfil de IVA Vendas para todas as linhas")
    external_id = invoice.billing_external_id or f"patas-{invoice.clinic_id}-invoice-{invoice.id}"
    return BillingPreviewPayload(
        external_id=external_id,
        store_external_id=invoice.issuer_store_external_id,
        document_date=local_today().isoformat(),
        lines=_billing_lines(invoice),
    )


def _tender_method(method: str) -> str:
    return {
        "cash": "CASH",
        "bank-transfer": "TRANSFER",
        "tpa": "CARD",
    }[method]


def build_billing_payload(invoice: Invoice) -> BillingInvoicePayload:
    if not invoice.issuer_name or not invoice.issuer_nif:
        raise ValueError("A clínica precisa de nome e NIF para emitir a fatura")
    if not invoice.issuer_store_external_id:
        raise ValueError("A clínica precisa do identificador de loja do Vendas")
    if not invoice.customer_name or not invoice.customer_nif:
        raise ValueError("O cliente precisa de nome e NIF para emitir a fatura")
    if not invoice.lines:
        raise ValueError("A fatura precisa de pelo menos uma linha")
    if not invoice.quote_id or invoice.quote_payable is None:
        raise ValueError("Calcule uma prévia fiscal no Vendas antes de emitir")
    external_id = invoice.billing_external_id or f"patas-{invoice.clinic_id}-invoice-{invoice.id}"
    idempotency_key = invoice.idempotency_key or str(uuid5(NAMESPACE_URL, external_id))
    payment = None
    if invoice.document_type == InvoiceDocumentType.INVOICE_RECEIPT:
        if not invoice.payment_method:
            raise ValueError("A fatura-recibo precisa de método de pagamento")
        if invoice.payment_method.value == "other":
            raise ValueError("O Vendas não aceita o método de pagamento 'outro' em FR")
        if invoice.payment_method.value == "cash" and not settings.VENDAS_CASH_SESSION_ID:
            raise ValueError("Pagamentos em numerário exigem uma sessão de caixa Vendas configurada")
        payment = BillingPayment(
            tenders=[
                BillingPaymentTender(
                    _tender_method(invoice.payment_method.value), invoice.quote_payable
                )
            ],
            external_reference=external_id,
            session_id=settings.VENDAS_CASH_SESSION_ID or None,
        )
    return BillingInvoicePayload(
        idempotency_key=idempotency_key,
        quote_id=invoice.quote_id,
        external_id=external_id,
        store_external_id=invoice.issuer_store_external_id,
        document_type=invoice.document_type.value,
        document_date=local_today().isoformat(),
        due_date=invoice.due_at.date().isoformat() if invoice.due_at else None,
        external_reference=f"appointment-{invoice.appointment_id}" if invoice.appointment_id else None,
        notes=invoice.description,
        customer=BillingParty(
            external_id=f"patas-owner-{invoice.owner_id}",
            name=invoice.customer_name,
            tax_id=invoice.customer_nif,
            country="AO",
            email=invoice.customer_email,
            phone=invoice.customer_phone,
            address=invoice.customer_address,
            final_consumer=False,
        ),
        lines=_billing_lines(invoice),
        payment=payment,
    )


class MockBillingAdapter:
    name = "mock"

    def preview_invoice(
        self, payload: BillingPreviewPayload, idempotency_key: str
    ) -> BillingQuoteResult:
        payable = sum(
            (line.quantity * line.unit_price for line in payload.lines), Decimal(0)
        )
        snapshot = {
            "quote": {
                "id": idempotency_key,
                "expiresAt": (datetime.now(UTC) + timedelta(minutes=10)).isoformat(),
                "vatConfigurationVersion": "mock-v1",
                "calculationDigest": f"mock-{idempotency_key}",
            },
            "totals": {"payable": float(payable)},
            "meta": {"mode": "TRAINING"},
        }
        return _quote_from_response(snapshot)

    def emit_invoice(self, payload: BillingInvoicePayload) -> BillingSyncResult:
        invoice_id = payload.external_id.rsplit("-", 1)[-1]
        return BillingSyncResult(
            external_reference=f"mock-patas-{invoice_id}",
            status="sent",
            document_number=f"MOCK-{int(invoice_id):06d}",
            series="MOCK",
            mode="TRAINING",
        )

    def get_status(self, external_reference: str) -> str:
        return "sent"


class VendasBillingAdapter:
    name = "vendas"

    def __init__(self) -> None:
        self.base_url = settings.VENDAS_BASE_URL.rstrip("/")
        self.headers = {"Authorization": f"Bearer {settings.VENDAS_API_KEY.get_secret_value()}"}

    def preview_invoice(
        self, payload: BillingPreviewPayload, idempotency_key: str
    ) -> BillingQuoteResult:
        response = httpx.post(
            f"{self.base_url}/api/integrations/v1/invoices/preview",
            json=payload.to_vendas_dict(),
            headers={**self.headers, "Idempotency-Key": idempotency_key},
            timeout=settings.VENDAS_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return _quote_from_response(response.json())

    def emit_invoice(self, payload: BillingInvoicePayload) -> BillingSyncResult:
        response = httpx.post(
            f"{self.base_url}/api/integrations/v1/invoices",
            json=payload.to_vendas_dict(),
            headers={**self.headers, "Idempotency-Key": payload.idempotency_key},
            timeout=settings.VENDAS_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        emitted = data["invoice"]
        return BillingSyncResult(
            external_reference=str(emitted["id"]),
            status=str(emitted.get("state", "ISSUED")),
            document_number=emitted.get("reference") or emitted.get("number"),
            series=emitted.get("seriesId"),
            document_url=emitted.get("documentUrl") or emitted.get("receiptUrl"),
            mode=emitted.get("mode"),
        )

    def get_status(self, external_reference: str) -> str:
        response = httpx.get(
            f"{self.base_url}/api/integrations/v1/invoices/{external_reference}",
            headers=self.headers,
            timeout=settings.VENDAS_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return str(response.json()["invoice"].get("state", "unknown"))


def is_paid_provider_state(state: str | None) -> bool:
    return bool(state) and state.strip().upper() in settings.VENDAS_PAID_STATES_SET


def get_billing_adapter() -> BillingAdapter:
    if settings.BILLING_PROVIDER == "mock":
        return MockBillingAdapter()
    if settings.BILLING_PROVIDER == "vendas":
        return VendasBillingAdapter()
    raise RuntimeError(f"Provedor de faturação não configurado: {settings.BILLING_PROVIDER}")


def _quote_from_response(data: dict) -> BillingQuoteResult:
    quote = data["quote"]
    expires_at = datetime.fromisoformat(str(quote["expiresAt"]))
    return BillingQuoteResult(
        quote_id=str(quote["id"]),
        expires_at=expires_at,
        vat_configuration_version=str(quote["vatConfigurationVersion"]),
        calculation_digest=str(quote["calculationDigest"]),
        payable=Decimal(str(data["totals"]["payable"])),
        snapshot=data,
    )


def _decimal_string(value: Decimal) -> str:
    return format(value, "f")


def _line_to_vendas_dict(line: BillingLinePayload) -> dict:
    payload = {
        "externalId": line.external_id,
        "code": line.code,
        "description": line.description,
        "kind": line.kind,
        "unit": line.unit,
        "vatProfileCode": line.vat_profile_code,
        "quantity": _decimal_string(line.quantity),
        "unitPrice": _decimal_string(line.unit_price),
        "discountPercent": _decimal_string(line.discount_percent),
    }
    if line.operation_type:
        payload["operationType"] = line.operation_type
    return payload
