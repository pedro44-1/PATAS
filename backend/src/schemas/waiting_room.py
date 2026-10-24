from datetime import datetime

from pydantic import BaseModel, Field

from src.models.waiting_room import WaitingRoomStatus


class WaitingRoomEntryCreate(BaseModel):
    appointment_id: int | None = None
    pet_id: int | None = None
    vet_id: int | None = None
    service_type_id: int | None = None
    scheduled_at: datetime | None = None
    duration_min: int = Field(default=30, ge=15, le=480)
    reason: str | None = Field(None, max_length=255)
    notes: str | None = Field(None, max_length=2000)
    room: str | None = Field(None, max_length=100)
    message: str | None = Field(None, max_length=255)


class WaitingRoomEntryUpdate(BaseModel):
    room: str | None = Field(None, max_length=100)
    message: str | None = Field(None, max_length=255)


class WaitingRoomTransition(BaseModel):
    status: WaitingRoomStatus
    reason: str | None = Field(None, max_length=255)


class WaitingRoomEntryResponse(BaseModel):
    id: int
    clinic_id: int
    appointment_id: int
    pet_id: int
    pet_name: str
    owner_id: int
    owner_name: str
    vet_id: int
    vet_name: str
    service_type_id: int | None
    service_type_name: str | None
    scheduled_at: datetime
    status: WaitingRoomStatus
    arrival_at: datetime
    called_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    room: str | None
    message: str | None
    status_reason: str | None
    reason: str | None
    notes: str | None

