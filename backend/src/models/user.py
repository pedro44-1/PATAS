from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from src.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    VET = "vet"
    RECEPTIONIST = "receptionist"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.RECEPTIONIST)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    clinic = relationship("Clinic", back_populates="users")
    appointments = relationship("Appointment", back_populates="vet")
