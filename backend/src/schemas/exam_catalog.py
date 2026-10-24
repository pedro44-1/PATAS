from datetime import datetime

from pydantic import BaseModel, Field

from src.models.clinical_exam import ExamFindingStatus


class ExamSystemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    sort_order: int = Field(default=0, ge=0)


class ExamSystemUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    sort_order: int | None = Field(None, ge=0)
    active: bool | None = None


class ExamFindingCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=180)
    sort_order: int = Field(default=0, ge=0)


class ExamFindingUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=180)
    sort_order: int | None = Field(None, ge=0)
    active: bool | None = None


class ExamFindingResponse(BaseModel):
    id: int
    clinic_id: int
    system_id: int
    name: str
    sort_order: int
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ExamSystemResponse(BaseModel):
    id: int
    clinic_id: int
    name: str
    sort_order: int
    active: bool
    created_at: datetime
    findings: list[ExamFindingResponse]


class ExamCatalogResponse(BaseModel):
    systems: list[ExamSystemResponse]


class ExamObservationInput(BaseModel):
    finding_id: int
    status: ExamFindingStatus
    note: str | None = Field(None, max_length=2000)


class ExamObservationResponse(BaseModel):
    id: int
    appointment_id: int
    finding_id: int
    finding_name: str
    system_id: int
    system_name: str
    status: ExamFindingStatus
    note: str | None
