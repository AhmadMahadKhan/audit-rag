# ===== app/models/user.py =====
from sqlalchemy import String, Boolean, ForeignKey, Table, Column, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel
from app.db.session import Base

user_roles = Table(
    "user_roles", Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)

role_permissions = Table(
    "role_permissions", Base.metadata,
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)

class User(BaseModel):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_login_attempts: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    roles: Mapped[list["Role"]] = relationship(secondary=user_roles, back_populates="users")

class Role(BaseModel):
    __tablename__ = "roles"
    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    users: Mapped[list["User"]] = relationship(secondary=user_roles, back_populates="roles")
    permissions: Mapped[list["Permission"]] = relationship(secondary=role_permissions, back_populates="roles")

class Permission(BaseModel):
    __tablename__ = "permissions"
    code: Mapped[str] = mapped_column(String, unique=True)  # e.g. "documents.read"
    description: Mapped[str] = mapped_column(String, nullable=True)
    roles: Mapped[list["Role"]] = relationship(secondary=role_permissions, back_populates="permissions")

class RefreshToken(BaseModel):
    __tablename__ = "refresh_tokens"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    device_info: Mapped[str] = mapped_column(String, nullable=True)

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String)
    ip_address: Mapped[str] = mapped_column(String, nullable=True)
    request_id: Mapped[str] = mapped_column(String, nullable=True)
    result: Mapped[str] = mapped_column(String)
    detail: Mapped[str] = mapped_column(String, nullable=True)
