from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.core.database import Base


class Pet(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    species = Column(String(100), nullable=False)  # Dog, Cat, Bird, etc.
    breed = Column(String(255), nullable=True)
    age = Column(String(50), nullable=True)  # e.g. "3 years", "6 months"
    weight = Column(Float, nullable=True)  # kg
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    clinic = relationship("Clinic", back_populates="pets")
    owner = relationship("Owner", back_populates="pets")
    appointments = relationship("Appointment", back_populates="pet")
