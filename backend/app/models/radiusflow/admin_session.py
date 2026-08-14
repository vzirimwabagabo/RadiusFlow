"""SQLAlchemy model for enterprise admin sessions stored in radiusflow.admin_sessions."""
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from database import Base


class AdminSession(Base):
    """A revocable session for an enterprise admin authenticated via radiusflow.admin_users."""

    __tablename__ = "admin_sessions"
    __table_args__ = {"schema": "radiusflow"}

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    admin_user_id = Column(
        BigInteger,
        ForeignKey("radiusflow.admin_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # SHA-256 hex digest of the raw bearer token — never store raw tokens
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    # Cached role name to avoid a join on every request resolution
    role_name = Column(String(64), nullable=False, default="super_admin")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship back to the admin user (lazy='joined' for efficient session resolution)
    admin_user = relationship(
        "AdminUser",
        foreign_keys=[admin_user_id],
        lazy="joined",
    )
