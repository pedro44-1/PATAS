import enum
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

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
    role = Column(
        Enum(UserRole, native_enum=False, values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
        default=UserRole.RECEPTIONIST,
    )
    must_change_password = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    clinic = relationship("Clinic", back_populates="users")
    appointments = relationship("Appointment", back_populates="vet")

    @property
    def clinic_name(self) -> str:
        return self.clinic.name
