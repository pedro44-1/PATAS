from sqlalchemy import Column, Integer, String

from app.core.database import Base


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    codename = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)