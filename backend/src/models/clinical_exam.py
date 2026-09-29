import enum
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from src.core.database import Base


class ExamFindingStatus(str, enum.Enum):
    NORMAL = "normal"
    ABNORMAL = "abnormal"
    NOT_EVALUATED = "not-evaluated"


class ClinicalExamSystem(Base):
    __tablename__ = "clinical_exam_systems"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    clinic = relationship("Clinic", back_populates="exam_systems")
    findings = relationship("ClinicalExamFinding", back_populates="system", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("clinic_id", "name", name="uq_exam_systems_clinic_name"),
        Index("ix_exam_systems_clinic_order", "clinic_id", "active", "sort_order"),
    )


class ClinicalExamFinding(Base):
    __tablename__ = "clinical_exam_findings"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    system_id = Column(Integer, ForeignKey("clinical_exam_systems.id"), nullable=False, index=True)
    name = Column(String(180), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    clinic = relationship("Clinic", back_populates="exam_findings")
    system = relationship("ClinicalExamSystem", back_populates="findings")
    observations = relationship("ClinicalExamObservation", back_populates="finding")

    __table_args__ = (
        UniqueConstraint("system_id", "name", name="uq_exam_findings_system_name"),
        Index("ix_exam_findings_clinic_active", "clinic_id", "active"),
    )


class ClinicalExamObservation(Base):
    __tablename__ = "clinical_exam_observations"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, index=True)
    finding_id = Column(Integer, ForeignKey("clinical_exam_findings.id"), nullable=False, index=True)
    finding_name = Column(String(180), nullable=False)
    status = Column(String(30), nullable=False, default=ExamFindingStatus.NOT_EVALUATED.value)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    clinic = relationship("Clinic", back_populates="exam_observations")
    appointment = relationship("Appointment", back_populates="exam_observations")
    finding = relationship("ClinicalExamFinding", back_populates="observations")

    __table_args__ = (
        UniqueConstraint("appointment_id", "finding_id", name="uq_exam_observations_appointment_finding"),
        Index("ix_exam_observations_clinic_appointment", "clinic_id", "appointment_id"),
    )
