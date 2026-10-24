import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.core.database import Base
from src.core.timezones import utc_now


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no-show"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False, index=True)
    vet_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False, index=True)
    service_type_id = Column(Integer, ForeignKey("service_types.id"), nullable=True, index=True)
    scheduled_at = Column(DateTime, nullable=False, index=True)
    duration_min = Column(Integer, nullable=False, default=30)
    status = Column(
        Enum(AppointmentStatus, native_enum=False, values_callable=lambda enum: [item.value for item in enum]),
        default=AppointmentStatus.SCHEDULED,
    )
    reason = Column(String(255), nullable=True)
    status_reason = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    weight = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    clinic = relationship("Clinic", back_populates="appointments")
    pet = relationship("Pet", back_populates="appointments")
    vet = relationship("User", back_populates="appointments")
    owner = relationship("Owner", back_populates="appointments")
    service_type = relationship("ServiceType", back_populates="appointments")
    waiting_room_entry = relationship("WaitingRoomEntry", back_populates="appointment", uselist=False)
    exam_observations = relationship("ClinicalExamObservation", back_populates="appointment", cascade="all, delete-orphan")
    treatment = relationship("Treatment", back_populates="appointment", uselist=False)
    invoice = relationship("Invoice", back_populates="appointment", uselist=False)

    @property
    def pet_name(self) -> str | None:
        return self.pet.name if self.pet else None

    @property
    def owner_name(self) -> str | None:
        return self.owner.name if self.owner else None

    @property
    def vet_name(self) -> str | None:
        return self.vet.name if self.vet else None

    @property
    def subject_archived(self) -> bool:
        return bool(
            (self.pet and self.pet.archived_at) or (self.owner and self.owner.archived_at)
        )
