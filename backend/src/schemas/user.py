from pydantic import BaseModel, EmailStr, field_validator, Field
from datetime import datetime

from src.models.user import UserRole


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.ADMIN

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("A password deve conter pelo menos uma letra maiГєscula")
        if not any(c.isdigit() for c in v):
            raise ValueError("A password deve conter pelo menos um nГєmero")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    clinic_id: int
    name: str
    email: str
    role: UserRole

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class UserRoleUpdate(BaseModel):
    role: UserRole