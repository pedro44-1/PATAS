
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.core.database import Base
from src.core.timezones import utc_now


class Treatment(Base):
    __tablename__ = "treatments"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), unique=True, nullable=False, index=True)
    diagnosis = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    prescription = Column(Text, nullable=True)
    anamnesis = Column(Text, nullable=True)
    consultation_type = Column(String(50), nullable=False, default="normal")
    referring_vet_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    clinic = relationship("Clinic", back_populates="treatments")
    appointment = relationship("Appointment", back_populates="treatment")
    referring_vet = relationship("User", foreign_keys=[referring_vet_id])
