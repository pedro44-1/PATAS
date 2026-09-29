from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.models.user import UserRole


def _validate_password(value: str) -> str:
    if not any(character.isupper() for character in value):
        raise ValueError("A palavra-passe deve conter pelo menos uma letra maiúscula")
    if not any(character.isdigit() for character in value):
        raise ValueError("A palavra-passe deve conter pelo menos um número")
    return value


class ClinicRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    clinic_name: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        return _validate_password(value)


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        return _validate_password(value)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    clinic_id: int
    name: str
    email: str
    role: UserRole
    clinic_name: str
    must_change_password: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class TokenRefresh(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    refresh_token: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        return _validate_password(value)


class UserRoleUpdate(BaseModel):
    role: UserRole
