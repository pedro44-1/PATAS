from pydantic import BaseModel, Field, model_validator
from datetime import datetime

from src.models.invoice import InvoiceStatus


class InvoiceCreate(BaseModel):
    owner_id: int
    appointment_id: int | None = None
    amount: float = Field(..., ge=0)
    description: str | None = Field(None, max_length=500)
    reason: str | None = Field(None, max_length=255)


class InvoiceUpdate(BaseModel):
    status: InvoiceStatus | None = None
    amount: float | None = Field(None, ge=0)
    description: str | None = Field(None, max_length=500)
    reason: str | None = Field(None, max_length=255)

    @model_validator(mode="after")
    def validate_cancelled_reason(self):
        if self.status == InvoiceStatus.CANCELLED and not self.reason:
            raise ValueError("reason Г© obrigatГіrio ao cancelar uma factura")
        return self


class InvoiceResponse(BaseModel):
    id: int
    clinic_id: int
    owner_id: int
    appointment_id: int | None
    amount: float
    status: InvoiceStatus
    description: str | None
    reason: str | None
    created_at: datetime

    class Config:
        from_attributes = True