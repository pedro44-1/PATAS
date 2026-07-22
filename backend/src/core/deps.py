import logging
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import decode_token
from src.services.cache import cache
from src.services.audit import audit
from src.models.user import User, UserRole
from src.models.permission import Permission
from src.models.role_permission import RolePermission

logger = logging.getLogger("patas.auth")
security = HTTPBearer()


class CurrentUser:
    def __init__(self, id: int, clinic_id: int, role: UserRole, email: str, name: str):
        self.id = id
        self.clinic_id = clinic_id
        self.role = role
        self.email = email
        self.name = name


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> CurrentUser:
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except Exception as e:
        logger.warning("Token decode failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invГЎlido ou expirado",
        )

    if await cache.is_token_blacklisted(payload.get("jti")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revogado",
        )

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning("User %s not found in DB", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilizador nГЈo encontrado",
        )

    role_enum = UserRole(user.role)
    return CurrentUser(
        id=user.id,
        clinic_id=user.clinic_id,
        role=role_enum,
        email=user.email,
        name=user.name,
    )


def require_permission(codename: str):
    def _check(
        request: Request,
        current_user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> CurrentUser:
        if current_user.role == UserRole.ADMIN:
            return current_user

        has = (
            db.query(RolePermission)
            .join(Permission, RolePermission.permission_id == Permission.id)
            .filter(
                RolePermission.role == current_user.role.value,
                Permission.codename == codename,
            )
            .first()
        )
        if not has:
            audit(
                db,
                clinic_id=current_user.clinic_id,
                user_id=current_user.id,
                action="FORBIDDEN",
                resource=codename,
                details={
                    "required_permission": codename,
                    "role": current_user.role.value,
                },
                ip_address=request.client.host if request else None,
            )
            logger.warning(
                "Permission denied: user=%s role=%s required=%s",
                current_user.id,
                current_user.role.value,
                codename,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="PermissГЈo negada",
            )
        return current_user

    return _check


def require_vet(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role not in (UserRole.VET, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas veterinГЎrios podem aceder a este recurso",
        )
    return current_user


def require_any_role(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user