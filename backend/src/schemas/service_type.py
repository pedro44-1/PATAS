from datetime import datetime

from pydantic import BaseModel, Field


class ServiceTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    sort_order: int = Field(default=0, ge=0)


class ServiceTypeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    sort_order: int | None = Field(None, ge=0)
    active: bool | None = None


class ServiceTypeResponse(BaseModel):
    id: int
    clinic_id: int
    name: str
    slug: str
    sort_order: int
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True
