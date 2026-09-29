from datetime import date, datetime

from pydantic import BaseModel, Field

from src.schemas.clinical import MedicationResponse
from src.schemas.exam_catalog import ExamObservationInput, ExamObservationResponse


class ClinicalMedicationLine(BaseModel):
    id: int | None = None
    name: str = Field(..., min_length=1, max_length=255)
    dosage: str = Field(..., min_length=1, max_length=255)
    frequency: str = Field(..., min_length=1, max_length=255)
    route: str = Field(..., min_length=1, max_length=100)
    start_date: date
    end_date: date | None = None
    instructions: str | None = Field(None, max_length=4000)
    notes: str | None = Field(None, max_length=4000)


class ClinicalRecordUpdate(BaseModel):
    anamnesis: str | None = Field(None, max_length=10000)
    diagnosis: str | None = Field(None, max_length=4000)
    notes: str | None = Field(None, max_length=4000)
    prescription: str | None = Field(None, max_length=4000)
    consultation_type: str = Field(default="normal", min_length=1, max_length=50)
    referring_vet_id: int | None = None
    exam_findings: list[ExamObservationInput] = Field(default_factory=list)
    medications: list[ClinicalMedicationLine] = Field(default_factory=list)


class ClinicalTreatmentResponse(BaseModel):
    id: int
    appointment_id: int
    diagnosis: str | None
    notes: str | None
    prescription: str | None
    anamnesis: str | None
    consultation_type: str
    referring_vet_id: int | None
    created_at: datetime
    updated_at: datetime | None


class ClinicalRecordResponse(BaseModel):
    appointment_id: int
    treatment: ClinicalTreatmentResponse | None
    exam_findings: list[ExamObservationResponse]
    medications: list[MedicationResponse]
