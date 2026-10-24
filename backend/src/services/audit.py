import json

from sqlalchemy.orm import Session

from src.core.timezones import utc_now
from src.models.audit_log import AuditLog


def audit(
    db: Session,
    clinic_id: int,
    user_id: int | None,
    action: str,
    resource: str,
    resource_id: int | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        clinic_id=clinic_id,
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        details=json.dumps(details, default=str) if details else None,
        ip_address=ip_address,
        created_at=utc_now(),
    )
    db.add(entry)
    db.commit()
    return entry