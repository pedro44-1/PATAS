from pydantic import BaseModel, Field
from datetime import datetime


class TreatmentCreate(BaseModel):
    appointment_id: int
    diagnosis: str | None = Field(None, max_length=2000)
    notes: str | None = Field(None, max_length=2000)
    prescription: str | None = Field(None, max_length=2000)


class TreatmentUpdate(BaseModel):
    diagnosis: str | None = Field(None, max_length=2000)
    notes: str | None = Field(None, max_length=2000)
    prescription: str | None = Field(None, max_length=2000)


class TreatmentResponse(BaseModel):
    id: int
    clinic_id: int
    appointment_id: int
    diagnosis: str | None
    notes: str | None
    prescription: str | None
    created_at: datetime

    class Config:
        from_attributes = True
