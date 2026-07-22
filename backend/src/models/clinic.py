from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from src.core.database import Base


class Clinic(Base):
    __tablename__ = "clinics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    users = relationship("User", back_populates="clinic")
    owners = relationship("Owner", back_populates="clinic")
    pets = relationship("Pet", back_populates="clinic")
    appointments = relationship("Appointment", back_populates="clinic")
    treatments = relationship("Treatment", back_populates="clinic")
    invoices = relationship("Invoice", back_populates="clinic")
