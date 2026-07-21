from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class OwnerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    address: str | None = Field(None, max_length=500)
    notes: str | None = Field(None, max_length=1000)


class OwnerUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    address: str | None = Field(None, max_length=500)
    notes: str | None = Field(None, max_length=1000)


class OwnerResponse(BaseModel):
    id: int
    clinic_id: int
    name: str
    phone: str | None
    email: str | None
    address: str | None
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True