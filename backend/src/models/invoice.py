import enum
from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship

from src.core.database import Base


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    CANCELLED = "cancelled"


class InvoiceSyncStatus(str, enum.Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank-transfer"
    TPA = "tpa"
    OTHER = "other"


class InvoiceDocumentType(str, enum.Enum):
    INVOICE = "FT"
    INVOICE_RECEIPT = "FR"


class InvoiceLineKind(str, enum.Enum):
    SERVICE = "SERVICE"
    PRODUCT = "PRODUCT"


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    subtotal = Column(Numeric(14, 2), nullable=False, default=0)
    tax_total = Column(Numeric(14, 2), nullable=False, default=0)
    status = Column(
        Enum(InvoiceStatus, native_enum=False, values_callable=lambda enum: [item.value for item in enum]),
        default=InvoiceStatus.DRAFT,
    )
    currency = Column(String(3), nullable=False, default="AOA")
    description = Column(String(500), nullable=True)
    document_type = Column(
        Enum(InvoiceDocumentType, native_enum=False, values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
        default=InvoiceDocumentType.INVOICE,
    )
    series = Column(String(64), nullable=True)
    document_number = Column(String(50), nullable=True)
    document_url = Column(String(1000), nullable=True)
    billing_external_id = Column(String(150), nullable=True, unique=True)
    idempotency_key = Column(String(36), nullable=True, unique=True)
    quote_id = Column(String(36), nullable=True, unique=True)
    quote_expires_at = Column(DateTime, nullable=True)
    quote_vat_configuration_version = Column(String(100), nullable=True)
    quote_calculation_digest = Column(String(255), nullable=True)
    quote_payable = Column(Numeric(14, 2), nullable=True)
    quote_snapshot = Column(Text, nullable=True)
    provider_status = Column(String(50), nullable=True)
    provider_mode = Column(String(30), nullable=True)
    sync_attempts = Column(Integer, nullable=False, default=0)
    last_sync_error = Column(String(500), nullable=True)
    last_sync_at = Column(DateTime, nullable=True)
    payment_method = Column(
        Enum(PaymentMethod, native_enum=False, values_callable=lambda enum: [item.value for item in enum]),
        nullable=True,
    )
    issued_at = Column(DateTime, nullable=True)
    due_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    issuer_name = Column(String(255), nullable=True)
    issuer_nif = Column(String(30), nullable=True)
    issuer_address = Column(String(500), nullable=True)
    issuer_phone = Column(String(50), nullable=True)
    issuer_store_external_id = Column(String(100), nullable=True)
    customer_name = Column(String(255), nullable=True)
    customer_nif = Column(String(30), nullable=True)
    customer_address = Column(String(500), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    customer_email = Column(String(255), nullable=True)
    reason = Column(String(255), nullable=True)
    external_reference = Column(String(255), nullable=True, unique=True)
    sync_status = Column(Enum(InvoiceSyncStatus), default=InvoiceSyncStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    clinic = relationship("Clinic", back_populates="invoices")
    owner = relationship("Owner", back_populates="invoices")
    appointment = relationship("Appointment", back_populates="invoice")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan", order_by="InvoiceLine.id")

    __table_args__ = (
        UniqueConstraint("clinic_id", "document_number", name="uq_invoices_clinic_document_number"),
        Index(
            "uq_invoices_active_appointment",
            "appointment_id",
            unique=True,
            postgresql_where=text("appointment_id IS NOT NULL AND status <> 'cancelled'"),
            sqlite_where=text("appointment_id IS NOT NULL AND status <> 'cancelled'"),
        ),
    )


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    code = Column(String(64), nullable=True)
    vat_profile_code = Column(String(80), nullable=True)
    kind = Column(
        Enum(InvoiceLineKind, native_enum=False, values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
        default=InvoiceLineKind.SERVICE,
    )
    unit = Column(String(12), nullable=False, default="UN")
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(14, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0)
    subtotal = Column(Numeric(14, 2), nullable=False)
    tax_amount = Column(Numeric(14, 2), nullable=False)
    total = Column(Numeric(14, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="lines")
    clinic = relationship("Clinic", back_populates="invoice_lines")
