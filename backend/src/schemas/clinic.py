from pydantic import BaseModel, Field, field_validator

from src.schemas.common import OptionalEmail, OptionalNif, OptionalPhone, OptionalText, reject_null


class ClinicCreate(BaseModel):
    name: str
    address: OptionalText = None
    phone: OptionalPhone = None
    email: OptionalEmail = None
    nif: OptionalNif = None


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
    phone: OptionalPhone = Field(None, max_length=50)
    email: OptionalEmail = None
    nif: OptionalNif = Field(None, max_length=30)
    billing_store_external_id: OptionalText = Field(None, max_length=100)

    @field_validator("name", mode="before")
    @classmethod
    def _reject_null(cls, value):
        return reject_null(value)
