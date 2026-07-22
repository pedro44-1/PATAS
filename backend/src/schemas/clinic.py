from pydantic import BaseModel, EmailStr


class ClinicCreate(BaseModel):
    name: str
    address: str | None = None
    phone: str | None = None
    email: EmailStr | None = None


class ClinicResponse(BaseModel):
    id: int
    name: str
    address: str | None
    phone: str | None
    email: str | None

    class Config:
        from_attributes = True
