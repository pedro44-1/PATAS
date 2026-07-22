from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from src.core.database import Base


class Treatment(Base):
    __tablename__ = "treatments"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), unique=True, nullable=False, index=True)
    diagnosis = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    prescription = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    clinic = relationship("Clinic", back_populates="treatments")
    appointment = relationship("Appointment", back_populates="treatment")
