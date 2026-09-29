import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.deps import CurrentUser, get_current_user_unrestricted
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.models.clinic import Clinic
from src.models.user import User, UserRole
from src.schemas.user import (
    ClinicRegistration,
    LogoutRequest,
    PasswordChange,
    Token,
    TokenRefresh,
    UserLogin,
    UserResponse,
)
from src.services.audit import audit
from src.services.cache import cache
from src.services.clinical_catalog import ensure_clinic_defaults

router = APIRouter()


def _claims(user: User) -> dict[str, str]:
    role = user.role.value if isinstance(user.role, UserRole) else user.role
    return {
        "sub": str(user.id),
        "clinic_id": str(user.clinic_id),
        "role": role,
    }


def _token_pair(user: User) -> Token:
    claims = _claims(user)
    return Token(
        access_token=create_access_token(claims),
        refresh_token=create_refresh_token(claims),
        must_change_password=user.must_change_password,
    )


def _decode_typed_token(token: str, expected_type: str) -> dict:
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    if payload.get("type") != expected_type:
        raise HTTPException(status_code=401, detail=f"Token não é um {expected_type} token")
    return payload


async def _blacklist_payload(payload: dict) -> None:
    jti = payload.get("jti")
    ttl = max(0, int(payload.get("exp", 0)) - int(time.time()))
    if jti and ttl > 0:
        await cache.blacklist_token(jti, ttl)


@router.post("/register", response_model=UserResponse)
def register(data: ClinicRegistration, db: Session = Depends(get_db), request: Request = None):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email já registado")

    clinic = Clinic(name=data.clinic_name.strip())
    db.add(clinic)
    db.flush()

    user = User(
        clinic_id=clinic.id,
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.ADMIN,
        must_change_password=False,
    )
    db.add(user)
    ensure_clinic_defaults(db, clinic.id, commit=False)
    db.commit()
    db.refresh(user)
    audit(
        db,
        clinic_id=clinic.id,
        user_id=user.id,
        action="CREATE",
        resource="user",
        resource_id=user.id,
        details={"email": user.email, "role": user.role.value},
        ip_address=request.client.host if request else None,
    )
    return user


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: Session = Depends(get_db), request: Request = None):
    ip = request.client.host if request else "unknown"
    rate_key = f"login:{ip}:{data.email.lower()}"
    allowed, _count = await cache.check_rate_limit(rate_key, 5, 60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login. Tente novamente em 60 segundos.",
        )

    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        if user:
            audit(
                db,
                clinic_id=user.clinic_id,
                user_id=user.id,
                action="LOGIN_FAILED",
                resource="user",
                resource_id=user.id,
                details={"email": data.email},
                ip_address=ip,
            )
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    audit(
        db,
        clinic_id=user.clinic_id,
        user_id=user.id,
        action="LOGIN",
        resource="user",
        resource_id=user.id,
        ip_address=ip,
    )
    return _token_pair(user)


@router.post("/refresh", response_model=Token)
async def refresh_token(data: TokenRefresh, db: Session = Depends(get_db), request: Request = None):
    ip = request.client.host if request else "unknown"
    payload = _decode_typed_token(data.refresh_token, "refresh")

    if await cache.is_token_blacklisted(payload.get("jti")):
        raise HTTPException(status_code=401, detail="Refresh token já utilizado")

    await _blacklist_payload(payload)

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilizador não encontrado")
    audit(
        db,
        clinic_id=user.clinic_id,
        user_id=user.id,
        action="TOKEN_REFRESH",
        resource="user",
        resource_id=user.id,
        ip_address=ip,
    )
    return _token_pair(user)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUser = Depends(get_current_user_unrestricted)):
    return UserResponse(
        id=current_user.id,
        clinic_id=current_user.clinic_id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        clinic_name=current_user.clinic_name,
        must_change_password=current_user.must_change_password,
    )


@router.post("/logout")
async def logout(
    data: LogoutRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user_unrestricted),
    db: Session = Depends(get_db),
):
    auth_header = request.headers.get("Authorization")
    access_payload = _decode_typed_token(auth_header.split(" ", 1)[1], "access")
    refresh_payload = _decode_typed_token(data.refresh_token, "refresh")
    if str(current_user.id) != str(refresh_payload.get("sub")):
        raise HTTPException(status_code=401, detail="O refresh token não pertence ao utilizador autenticado")
    await _blacklist_payload(access_payload)
    await _blacklist_payload(refresh_payload)
    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="LOGOUT",
        resource="user",
        resource_id=current_user.id,
        ip_address=request.client.host if request else None,
    )
    return {"ok": True, "message": "Sessão terminada"}


@router.post("/change-password", response_model=Token)
async def change_password(
    data: PasswordChange,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user_unrestricted),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Palavra-passe atual inválida")
    refresh_payload = _decode_typed_token(data.refresh_token, "refresh")
    if await cache.is_token_blacklisted(refresh_payload.get("jti")):
        raise HTTPException(status_code=401, detail="Refresh token já utilizado")
    if str(user.id) != str(refresh_payload.get("sub")):
        raise HTTPException(status_code=401, detail="O refresh token não pertence ao utilizador autenticado")
    auth_header = request.headers.get("Authorization", "")
    access_payload = _decode_typed_token(auth_header.split(" ", 1)[1], "access")

    user.password_hash = hash_password(data.new_password)
    user.must_change_password = False
    db.commit()
    db.refresh(user)
    await _blacklist_payload(access_payload)
    await _blacklist_payload(refresh_payload)
    audit(
        db,
        clinic_id=user.clinic_id,
        user_id=user.id,
        action="PASSWORD_CHANGE",
        resource="user",
        resource_id=user.id,
        ip_address=request.client.host if request else None,
    )
    return _token_pair(user)
