import enum
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String
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


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    status = Column(
        Enum(InvoiceStatus, native_enum=False, values_callable=lambda enum: [item.value for item in enum]),
        default=InvoiceStatus.DRAFT,
    )
    currency = Column(String(3), nullable=False, default="AOA")
    description = Column(String(500), nullable=True)
    reason = Column(String(255), nullable=True)
    external_reference = Column(String(255), nullable=True, unique=True)
    sync_status = Column(Enum(InvoiceSyncStatus), default=InvoiceSyncStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    clinic = relationship("Clinic", back_populates="invoices")
    owner = relationship("Owner", back_populates="invoices")
    appointment = relationship("Appointment", back_populates="invoice")
