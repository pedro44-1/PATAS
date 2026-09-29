import logging

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import decode_token
from src.models.permission import Permission
from src.models.role_permission import RolePermission
from src.models.user import User, UserRole
from src.services.audit import audit
from src.services.cache import cache

logger = logging.getLogger("patas.auth")
security = HTTPBearer()


class CurrentUser:
    def __init__(
        self,
        id: int,
        clinic_id: int,
        role: UserRole,
        email: str,
        name: str,
        clinic_name: str,
        must_change_password: bool,
    ):
        self.id = id
        self.clinic_id = clinic_id
        self.role = role
        self.email = email
        self.name = name
        self.clinic_name = clinic_name
        self.must_change_password = must_change_password


async def get_current_user_unrestricted(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> CurrentUser:
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except JWTError as e:
        logger.warning("Token decode failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso inválido",
        )

    if await cache.is_token_blacklisted(payload.get("jti")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revogado",
        )

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning("User %s not found in DB", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilizador não encontrado",
        )

    role_enum = UserRole(user.role)
    return CurrentUser(
        id=user.id,
        clinic_id=user.clinic_id,
        role=role_enum,
        email=user.email,
        name=user.name,
        clinic_name=user.clinic.name,
        must_change_password=user.must_change_password,
    )


async def get_current_user(
    current_user: CurrentUser = Depends(get_current_user_unrestricted),
) -> CurrentUser:
    if current_user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PASSWORD_CHANGE_REQUIRED",
        )
    return current_user


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
                detail="Permissão negada",
            )
        return current_user

    return _check


def require_vet(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role not in (UserRole.VET, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas veterinários podem aceder a este recurso",
        )
    return current_user


def require_any_role(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user
