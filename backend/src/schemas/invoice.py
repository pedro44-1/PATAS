from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from src.models.invoice import (
    InvoiceDocumentType,
    InvoiceLineKind,
    InvoiceStatus,
    InvoiceSyncStatus,
    PaymentMethod,
)


class InvoiceLineCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    code: str | None = Field(None, max_length=64)
    vat_profile_code: str | None = Field(None, max_length=80)
    kind: InvoiceLineKind = InvoiceLineKind.SERVICE
    unit: str = Field("UN", min_length=1, max_length=12)
    quantity: Decimal = Field(Decimal(1), gt=0, decimal_places=3)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)
    tax_rate: Decimal = Field(Decimal(0), ge=0, le=0, decimal_places=2)


class InvoiceLineResponse(InvoiceLineCreate):
    id: int
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal

    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    owner_id: int
    appointment_id: int | None = None
    amount: Decimal | None = Field(None, ge=0, decimal_places=2)
    description: str | None = Field(None, max_length=500)
    items: list[InvoiceLineCreate] = Field(default_factory=list, max_length=100)
    document_type: InvoiceDocumentType = InvoiceDocumentType.INVOICE
    payment_method: PaymentMethod | None = None
    due_at: datetime | None = None

    @model_validator(mode="after")
    def validate_lines_or_legacy_amount(self):
        if not self.items and self.amount is None:
            raise ValueError("É necessário indicar pelo menos uma linha")
        if not self.items and not self.description:
            self.description = "Serviços veterinários"
        if self.document_type == InvoiceDocumentType.INVOICE_RECEIPT and not self.payment_method:
            raise ValueError("O método de pagamento é obrigatório para fatura-recibo")
        return self


class InvoiceUpdate(BaseModel):
    status: InvoiceStatus | None = None
    amount: Decimal | None = Field(None, ge=0, decimal_places=2)
    description: str | None = Field(None, max_length=500)
    reason: str | None = Field(None, max_length=255)
    payment_method: PaymentMethod | None = None

    @model_validator(mode="after")
    def validate_cancelled_reason(self):
        if self.status == InvoiceStatus.CANCELLED and not self.reason:
            raise ValueError("reason é obrigatório ao cancelar uma factura")
        return self


class InvoiceResponse(BaseModel):
    id: int
    clinic_id: int
    owner_id: int
    appointment_id: int | None
    amount: float
    subtotal: Decimal
    tax_total: Decimal
    status: InvoiceStatus
    currency: str
    description: str | None
    document_type: InvoiceDocumentType
    series: str | None
    document_number: str | None
    document_url: str | None
    billing_external_id: str | None
    idempotency_key: str | None
    quote_id: str | None
    quote_expires_at: datetime | None
    quote_vat_configuration_version: str | None
    quote_calculation_digest: str | None
    quote_payable: Decimal | None
    provider_status: str | None
    provider_mode: str | None
    sync_attempts: int
    last_sync_error: str | None
    last_sync_at: datetime | None
    payment_method: PaymentMethod | None
    issued_at: datetime | None
    due_at: datetime | None
    paid_at: datetime | None
    issuer_name: str | None
    issuer_nif: str | None
    issuer_address: str | None
    issuer_phone: str | None
    issuer_store_external_id: str | None
    customer_name: str | None
    customer_nif: str | None
    customer_address: str | None
    customer_phone: str | None
    customer_email: str | None
    reason: str | None
    external_reference: str | None
    sync_status: InvoiceSyncStatus
    created_at: datetime
    items: list[InvoiceLineResponse] = Field(validation_alias="lines")

    class Config:
        from_attributes = True
