from typing import Any

from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    skip: int = 0
    limit: int = 100