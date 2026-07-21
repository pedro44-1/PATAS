from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint

from app.core.database import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(50), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("role", "permission_id", name="uq_role_permission"),
    )