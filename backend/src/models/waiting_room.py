import enum
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from src.core.database import Base


class WaitingRoomStatus(str, enum.Enum):
    WAITING = "waiting"
    CALLED = "called"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no-show"


class WaitingRoomEntry(Base):
    __tablename__ = "waiting_room_entries"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, index=True)
    status = Column(String(30), nullable=False, default=WaitingRoomStatus.WAITING.value, index=True)
    arrival_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    called_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    room = Column(String(100), nullable=True)
    message = Column(String(255), nullable=True)
    status_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    clinic = relationship("Clinic", back_populates="waiting_room_entries")
    appointment = relationship("Appointment", back_populates="waiting_room_entry")

    __table_args__ = (
        UniqueConstraint("clinic_id", "appointment_id", name="uq_waiting_room_clinic_appointment"),
        Index("ix_waiting_room_clinic_arrival", "clinic_id", "arrival_at"),
    )
