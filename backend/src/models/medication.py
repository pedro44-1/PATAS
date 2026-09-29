import enum
from datetime import UTC, datetime

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from src.core.database import Base


class MedicationStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    VOIDED = "voided"


class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    vet_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    dosage = Column(String(255), nullable=False)
    frequency = Column(String(255), nullable=False)
    route = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True)
    instructions = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(Enum(MedicationStatus), nullable=False, default=MedicationStatus.ACTIVE)
    void_reason = Column(String(1000), nullable=True)
    voided_at = Column(DateTime, nullable=True)
    voided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    clinic = relationship("Clinic")
    pet = relationship("Pet", back_populates="medications")
    appointment = relationship("Appointment")
    vet = relationship("User", foreign_keys=[vet_id])
    voided_by_user = relationship("User", foreign_keys=[voided_by])

    __table_args__ = (
        Index("ix_medications_clinic_pet_date", "clinic_id", "pet_id", "start_date"),
    )
