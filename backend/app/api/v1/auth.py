from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from jose import jwt

from app.core.database import get_db
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.deps import CurrentUser, get_current_user
from app.services.cache import cache
from app.services.audit import audit
from app.models.clinic import Clinic
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, TokenRefresh

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register(data: UserCreate, db: Session = Depends(get_db), request: Request = None):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email já registado")

    # Create new clinic for this registration (SaaS multi-tenant pattern)
    clinic = Clinic(name=f"Clínica {data.name}")
    db.add(clinic)
    db.commit()
    db.refresh(clinic)

    user = User(
        clinic_id=clinic.id,
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
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
    rate_key = f"login:{ip}"
    allowed, count = await cache.check_rate_limit(rate_key, 5, 60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login. Tente novamente em 60 segundos.",
        )

    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        audit(
            db,
            clinic_id=user.clinic_id if user else 0,
            user_id=user.id if user else 0,
            action="LOGIN_FAILED",
            resource="user",
            resource_id=user.id if user else None,
            details={"email": data.email},
            ip_address=ip,
        )
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    access = create_access_token({
        "sub": str(user.id),
        "clinic_id": str(user.clinic_id),
        "role": user.role.value,
    })
    refresh = create_refresh_token({
        "sub": str(user.id),
        "clinic_id": str(user.clinic_id),
        "role": user.role.value,
    })
    audit(
        db,
        clinic_id=user.clinic_id,
        user_id=user.id,
        action="LOGIN",
        resource="user",
        resource_id=user.id,
        ip_address=ip,
    )
    return Token(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=Token)
async def refresh_token(data: TokenRefresh, db: Session = Depends(get_db), request: Request = None):
    ip = request.client.host if request else "unknown"
    try:
        payload = decode_token(data.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token não é um refresh token")

    if await cache.is_token_blacklisted(payload.get("jti")):
        raise HTTPException(status_code=401, detail="Refresh token já utilizado")

    await cache.blacklist_token(payload["jti"], settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400)

    sub = payload["sub"]
    clinic_id = payload["clinic_id"]
    role = payload["role"]

    access = create_access_token({"sub": sub, "clinic_id": clinic_id, "role": role})
    refresh = create_refresh_token({"sub": sub, "clinic_id": clinic_id, "role": role})
    audit(
        db,
        clinic_id=int(clinic_id),
        user_id=int(sub),
        action="TOKEN_REFRESH",
        resource="user",
        resource_id=int(sub),
        ip_address=ip,
    )
    return Token(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUser = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        clinic_id=current_user.clinic_id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
    )


@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    token = auth_header.split(" ")[1]
    try:
        payload = decode_token(token)
        jti = payload.get("jti")
        if jti:
            import time
            exp = payload.get("exp", 0)
            ttl = max(0, exp - int(time.time()))
            if ttl > 0:
                await cache.blacklist_token(jti, ttl)
        audit(
            db,
            clinic_id=payload.get("clinic_id", 0),
            user_id=payload.get("sub", 0),
            action="LOGOUT",
            resource="user",
            resource_id=payload.get("sub", 0),
            ip_address=request.client.host if request else None,
        )
    except Exception:
        pass  # Token invalid, nothing to blacklist
    
    return {"ok": True, "message": "Logged out"}
