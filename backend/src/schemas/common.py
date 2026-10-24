import re
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


ANGOLA_NIF = re.compile(r"^(\d{10}|\d{9}[A-Z]{2}\d{3})$")
PHONE_NUMBER = re.compile(r"^(\+\d{8,15}|\d{9})$")


def normalize_nif(value: Any) -> Any:
    value = blank_to_none(value)
    if value is None:
        return None
    compact = re.sub(r"[\s.\-]", "", str(value)).upper()
    if not ANGOLA_NIF.match(compact):
        raise ValueError(
            "NIF inválido: use 10 dígitos (empresa) ou 9 dígitos, 2 letras e 3 dígitos (pessoa singular)"
        )
    return compact


def normalize_phone(value: Any) -> Any:
    value = blank_to_none(value)
    if value is None:
        return None
    text = " ".join(str(value).split())
    if not PHONE_NUMBER.match(re.sub(r"[\s().\-]", "", text)):
        raise ValueError("Telefone inválido: use 9 dígitos ou o formato internacional (+244 ...)")
    return text


OptionalText = Annotated[str | None, BeforeValidator(blank_to_none)]
OptionalEmail = Annotated[EmailStr | None, BeforeValidator(blank_to_none)]
OptionalNif = Annotated[str | None, BeforeValidator(normalize_nif)]
OptionalPhone = Annotated[str | None, BeforeValidator(normalize_phone)]


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    skip: int = 0
    limit: int = 100
