from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.schemas.common import OptionalEmail, OptionalNif, OptionalPhone, OptionalText, reject_null


class OwnerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: OptionalPhone = Field(None, max_length=20)
    email: OptionalEmail = None
    address: OptionalText = Field(None, max_length=500)
    nif: OptionalNif = Field(None, max_length=30)
    notes: OptionalText = Field(None, max_length=1000)


class OwnerUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    phone: OptionalPhone = Field(None, max_length=20)
    email: OptionalEmail = None
    address: OptionalText = Field(None, max_length=500)
    nif: OptionalNif = Field(None, max_length=30)
    notes: OptionalText = Field(None, max_length=1000)

    @field_validator("name", mode="before")
    @classmethod
    def _reject_null(cls, value):
        return reject_null(value)


class OwnerResponse(BaseModel):
    id: int
    clinic_id: int
    name: str
    phone: str | None
    email: str | None
    address: str | None
    nif: str | None
    notes: str | None
    archived_at: datetime | None
    archived_by_user_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True
