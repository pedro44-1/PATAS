from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from src.core.config import settings


def utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=ZoneInfo(settings.APP_TIMEZONE))
    return value.astimezone(UTC).replace(tzinfo=None)


def local_today() -> date:
    return datetime.now(ZoneInfo(settings.APP_TIMEZONE)).date()


def local_day_bounds(value: str | None, *, error_detail: str = "Data inválida") -> tuple[datetime, datetime]:
    try:
        target = date.fromisoformat(value) if value else local_today()
    except ValueError:
        raise HTTPException(status_code=422, detail=error_detail)
    local_zone = ZoneInfo(settings.APP_TIMEZONE)
    local_start = datetime.combine(target, time.min, tzinfo=local_zone)
    local_end = datetime.combine(target.fromordinal(target.toordinal() + 1), time.min, tzinfo=local_zone)
    return utc_naive(local_start), utc_naive(local_end)
