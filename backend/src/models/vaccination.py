import enum
from datetime import UTC, datetime

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from src.core.database import Base


class VaccinationStatus(str, enum.Enum):
    ADMINISTERED = "administered"
    VOIDED = "voided"


class Vaccination(Base):
    __tablename__ = "vaccinations"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    vet_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    administered_at = Column(DateTime, nullable=False, index=True)
    dose = Column(String(100), nullable=False)
    lot_number = Column(String(100), nullable=True)
    expires_at = Column(Date, nullable=True)
    next_due_at = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(Enum(VaccinationStatus), nullable=False, default=VaccinationStatus.ADMINISTERED)
    void_reason = Column(String(1000), nullable=True)
    voided_at = Column(DateTime, nullable=True)
    voided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    clinic = relationship("Clinic")
    pet = relationship("Pet", back_populates="vaccinations")
    appointment = relationship("Appointment")
    vet = relationship("User", foreign_keys=[vet_id])
    voided_by_user = relationship("User", foreign_keys=[voided_by])

    __table_args__ = (
        Index("ix_vaccinations_clinic_pet_date", "clinic_id", "pet_id", "administered_at"),
    )
