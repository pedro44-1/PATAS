from datetime import UTC, datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.core.database import Base


class Pet(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    species = Column(String(100), nullable=False)
    breed = Column(String(255), nullable=True)
    birth_date = Column(Date, nullable=True)
    weight = Column(Float, nullable=True)  # kg — latest recorded weight
    notes = Column(Text, nullable=True)
    archived_at = Column(DateTime, nullable=True, index=True)
    archived_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    clinic = relationship("Clinic", back_populates="pets")
    owner = relationship("Owner", back_populates="pets")
    appointments = relationship("Appointment", back_populates="pet")
    vaccinations = relationship("Vaccination", back_populates="pet")
    medications = relationship("Medication", back_populates="pet")
