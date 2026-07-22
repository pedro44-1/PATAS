from pydantic import BaseModel, Field
from datetime import datetime, date


class PetCreate(BaseModel):
    owner_id: int
    name: str = Field(..., min_length=1, max_length=100)
    species: str = Field(..., min_length=1, max_length=50)
    breed: str | None = Field(None, max_length=100)
    birth_date: date | None = None
    weight: float | None = Field(None, ge=0)
    notes: str | None = Field(None, max_length=1000)


class PetUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    species: str | None = Field(None, min_length=1, max_length=50)
    breed: str | None = Field(None, max_length=100)
    birth_date: date | None = None
    weight: float | None = Field(None, ge=0)
    notes: str | None = Field(None, max_length=1000)


class PetResponse(BaseModel):
    id: int
    clinic_id: int
    owner_id: int
    name: str
    species: str
    breed: str | None
    birth_date: date | None
    weight: float | None
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True
