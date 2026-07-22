from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from src.core.database import get_db
from src.core.deps import CurrentUser, get_current_user, require_permission
from src.models.user import User
from src.schemas.user import UserResponse, UserRoleUpdate
from src.services.audit import audit

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def list_users(
    response: Response,
    skip: int = 0,
    limit: int = 100,
    current_user: CurrentUser = Depends(require_permission("user:read")),
    db: Session = Depends(get_db),
):
    query = db.query(User).filter(User.clinic_id == current_user.clinic_id)
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    response.headers["X-Total-Count"] = str(total)
    return users


@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    data: UserRoleUpdate,
    current_user: CurrentUser = Depends(require_permission("user:write")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400, detail="NГЈo pode alterar a sua prГіpria funГ§ГЈo"
        )

    user = db.query(User).filter(
        User.id == user_id, User.clinic_id == current_user.clinic_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador nГЈo encontrado")

    old_role = user.role
    user.role = data.role
    db.commit()
    db.refresh(user)

    audit(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        action="UPDATE",
        resource="user",
        resource_id=user.id,
        details={"old_role": old_role.value, "new_role": user.role.value},
        ip_address=request.client.host if request else None,
    )
    return user