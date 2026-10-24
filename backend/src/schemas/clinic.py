from pydantic import BaseModel, Field

from src.schemas.common import OptionalEmail, OptionalText


class ClinicCreate(BaseModel):
    name: str
    address: OptionalText = None
    phone: OptionalText = None
    email: OptionalEmail = None
    nif: OptionalText = None


class ClinicResponse(BaseModel):
    id: int
    name: str
    address: str | None
    phone: str | None
    email: str | None
    nif: str | None
    billing_store_external_id: str | None

    class Config:
        from_attributes = True


class ClinicUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    address: OptionalText = Field(None, max_length=500)
    phone: OptionalText = Field(None, max_length=50)
    email: OptionalEmail = None
    nif: OptionalText = Field(None, max_length=30)
    billing_store_external_id: OptionalText = Field(None, max_length=100)
