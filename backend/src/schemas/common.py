from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, EmailStr


def blank_to_none(value: Any) -> Any:
    if isinstance(value, str) and not value.strip():
        return None
    return value


def reject_null(value: Any) -> Any:
    if value is None:
        raise ValueError("Este campo não pode ser nulo")
    return value


OptionalText = Annotated[str | None, BeforeValidator(blank_to_none)]
OptionalEmail = Annotated[EmailStr | None, BeforeValidator(blank_to_none)]


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    skip: int = 0
    limit: int = 100
