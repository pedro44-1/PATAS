from datetime import datetime

from pydantic import BaseModel, Field

from src.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    pet_id: int
    vet_id: int
    scheduled_at: datetime
    duration_min: int = Field(default=30, ge=15, le=480)
    reason: str | None = Field(None, max_length=255)
    notes: str | None = Field(None, max_length=2000)
    weight: float | None = Field(None, ge=0)
    service_type_id: int | None = None


class AppointmentUpdate(BaseModel):
    pet_id: int | None = None
    vet_id: int | None = None
    scheduled_at: datetime | None = None
    duration_min: int | None = Field(None, ge=15, le=480)
    status: AppointmentStatus | None = None
    status_reason: str | None = Field(None, max_length=255)
    reason: str | None = Field(None, max_length=255)
    notes: str | None = Field(None, max_length=2000)
    weight: float | None = Field(None, ge=0)
    service_type_id: int | None = None


class AppointmentResponse(BaseModel):
    id: int
    clinic_id: int
    pet_id: int
    vet_id: int
    owner_id: int
    scheduled_at: datetime
    duration_min: int
    status: AppointmentStatus
    status_reason: str | None
    reason: str | None
    notes: str | None
    weight: float | None
    service_type_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True
