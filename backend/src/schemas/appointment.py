from pydantic import BaseModel, Field
from datetime import datetime

from src.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    pet_id: int
    vet_id: int
    scheduled_at: datetime
    duration_min: int = Field(default=30, ge=15, le=480)
    reason: str | None = Field(None, max_length=255)
    notes: str | None = Field(None, max_length=2000)
    weight: float | None = Field(None, ge=0)


class AppointmentUpdate(BaseModel):
    scheduled_at: datetime | None = None
    duration_min: int | None = Field(None, ge=15, le=480)
    status: AppointmentStatus | None = None
    reason: str | None = Field(None, max_length=255)
    notes: str | None = Field(None, max_length=2000)
    weight: float | None = Field(None, ge=0)


class AppointmentResponse(BaseModel):
    id: int
    clinic_id: int
    pet_id: int
    vet_id: int
    owner_id: int
    scheduled_at: datetime
    duration_min: int
    status: AppointmentStatus
    reason: str | None
    notes: str | None
    weight: float | None
    created_at: datetime

    class Config:
        from_attributes = True