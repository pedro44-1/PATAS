from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from src.core.database import Base


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no-show"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False, index=True)
    vet_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False, index=True)
    scheduled_at = Column(DateTime, nullable=False, index=True)
    duration_min = Column(Integer, default=30)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    reason = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    weight = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    clinic = relationship("Clinic", back_populates="appointments")
    pet = relationship("Pet", back_populates="appointments")
    vet = relationship("User", back_populates="appointments")
    owner = relationship("Owner", back_populates="appointments")
    treatment = relationship("Treatment", back_populates="appointment", uselist=False)
    invoice = relationship("Invoice", back_populates="appointment", uselist=False)
