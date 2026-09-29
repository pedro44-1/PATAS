from datetime import datetime

from pydantic import BaseModel, Field


class TreatmentCreate(BaseModel):
    appointment_id: int
    diagnosis: str | None = Field(None, max_length=2000)
    notes: str | None = Field(None, max_length=2000)
    prescription: str | None = Field(None, max_length=2000)
    anamnesis: str | None = Field(None, max_length=10000)
    consultation_type: str = Field(default="normal", min_length=1, max_length=50)
    referring_vet_id: int | None = None


class TreatmentUpdate(BaseModel):
    diagnosis: str | None = Field(None, max_length=2000)
    notes: str | None = Field(None, max_length=2000)
    prescription: str | None = Field(None, max_length=2000)
    anamnesis: str | None = Field(None, max_length=10000)
    consultation_type: str | None = Field(None, min_length=1, max_length=50)
    referring_vet_id: int | None = None


class TreatmentResponse(BaseModel):
    id: int
    clinic_id: int
    appointment_id: int
    diagnosis: str | None
    notes: str | None
    prescription: str | None
    anamnesis: str | None
    consultation_type: str
    referring_vet_id: int | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True
