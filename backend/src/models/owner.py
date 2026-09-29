from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.core.database import Base


class Owner(Base):
    __tablename__ = "owners"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    archived_at = Column(DateTime, nullable=True, index=True)
    archived_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    clinic = relationship("Clinic", back_populates="owners")
    pets = relationship("Pet", back_populates="owner")
    appointments = relationship("Appointment", back_populates="owner")
    invoices = relationship("Invoice", back_populates="owner")
