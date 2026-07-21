from typing import Any


def safe_update(instance: Any, data: dict, allowed_fields: set[str]) -> None:
    for field in allowed_fields:
        if field in data:
            setattr(instance, field, data[field])