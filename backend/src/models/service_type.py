
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.core.database import Base
from src.core.timezones import utc_now


class ServiceType(Base):
    __tablename__ = "service_types"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=utc_now)

    clinic = relationship("Clinic", back_populates="service_types")
    appointments = relationship("Appointment", back_populates="service_type")

    __table_args__ = (
        UniqueConstraint("clinic_id", "slug", name="uq_service_types_clinic_slug"),
        Index("ix_service_types_clinic_active_order", "clinic_id", "active", "sort_order"),
    )
