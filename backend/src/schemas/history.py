from datetime import datetime

from pydantic import BaseModel

from src.models.appointment import AppointmentStatus
from src.schemas.clinical import MedicationResponse, VaccinationResponse
from src.schemas.exam_catalog import ExamObservationResponse


class HistoryTreatment(BaseModel):
    id: int
    created_at: datetime
    diagnosis: str | None
    prescription: str | None
    notes: str | None
    anamnesis: str | None
    consultation_type: str
    referring_vet_id: int | None

    class Config:
        from_attributes = True


class HistoryAppointment(BaseModel):
    id: int
    scheduled_at: datetime
    vet_id: int
    reason: str | None
    status: AppointmentStatus
    status_reason: str | None
    weight: float | None
    notes: str | None
    treatment: HistoryTreatment | None
    service_type_id: int | None
    service_type_name: str | None
    exam_findings: list[ExamObservationResponse]


class PetHistoryResponse(BaseModel):
    pet_id: int
    appointments: list[HistoryAppointment]
    vaccinations: list[VaccinationResponse]
    medications: list[MedicationResponse]
