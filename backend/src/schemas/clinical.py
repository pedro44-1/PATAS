from datetime import UTC, date, datetime

from pydantic import BaseModel, Field

from src.models.medication import MedicationStatus
from src.models.vaccination import VaccinationStatus


class VaccinationCreate(BaseModel):
    pet_id: int
    vet_id: int
    appointment_id: int | None = None
    name: str = Field(..., min_length=1, max_length=255)
    administered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    dose: str = Field(..., min_length=1, max_length=100)
    lot_number: str | None = Field(None, max_length=100)
    expires_at: date | None = None
    next_due_at: date | None = None
    notes: str | None = Field(None, max_length=4000)


class VaccinationUpdate(BaseModel):
    vet_id: int | None = None
    appointment_id: int | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    administered_at: datetime | None = None
    dose: str | None = Field(None, min_length=1, max_length=100)
    lot_number: str | None = Field(None, max_length=100)
    expires_at: date | None = None
    next_due_at: date | None = None
    notes: str | None = Field(None, max_length=4000)


class MedicationCreate(BaseModel):
    pet_id: int
    vet_id: int
    appointment_id: int | None = None
    name: str = Field(..., min_length=1, max_length=255)
    dosage: str = Field(..., min_length=1, max_length=255)
    frequency: str = Field(..., min_length=1, max_length=255)
    route: str = Field(..., min_length=1, max_length=100)
    start_date: date
    end_date: date | None = None
    instructions: str | None = Field(None, max_length=4000)
    notes: str | None = Field(None, max_length=4000)


class MedicationUpdate(BaseModel):
    vet_id: int | None = None
    appointment_id: int | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    dosage: str | None = Field(None, min_length=1, max_length=255)
    frequency: str | None = Field(None, min_length=1, max_length=255)
    route: str | None = Field(None, min_length=1, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    instructions: str | None = Field(None, max_length=4000)
    notes: str | None = Field(None, max_length=4000)
    status: MedicationStatus | None = None


class ClinicalVoidRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000)


class VaccinationResponse(BaseModel):
    id: int
    clinic_id: int
    pet_id: int
    appointment_id: int | None
    vet_id: int
    vet_name: str | None = None
    name: str
    administered_at: datetime
    dose: str
    lot_number: str | None
    expires_at: date | None
    next_due_at: date | None
    notes: str | None
    status: VaccinationStatus
    void_reason: str | None
    voided_at: datetime | None
    created_at: datetime
    updated_at: datetime | None


class MedicationResponse(BaseModel):
    id: int
    clinic_id: int
    pet_id: int
    appointment_id: int | None
    vet_id: int
    vet_name: str | None = None
    name: str
    dosage: str
    frequency: str
    route: str
    start_date: date
    end_date: date | None
    instructions: str | None
    notes: str | None
    status: MedicationStatus
    void_reason: str | None
    voided_at: datetime | None
    created_at: datetime
    updated_at: datetime | None

