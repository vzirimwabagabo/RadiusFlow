from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship
from database import Base


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "radiusflow"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = {"schema": "radiusflow"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = {"schema": "radiusflow"}

    role_id = Column(Integer, ForeignKey("radiusflow.roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("radiusflow.permissions.id", ondelete="CASCADE"), primary_key=True)


class AdminUser(Base):
    __tablename__ = "admin_users"
    __table_args__ = {"schema": "radiusflow"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    full_name = Column(String(128), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=True)
    failed_login_count = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    roles = relationship("Role", secondary="radiusflow.admin_user_roles", backref="admin_users")


class AdminUserRole(Base):
    __tablename__ = "admin_user_roles"
    __table_args__ = {"schema": "radiusflow"}

    admin_user_id = Column(Integer, ForeignKey("radiusflow.admin_users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("radiusflow.roles.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
