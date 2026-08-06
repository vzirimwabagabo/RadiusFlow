"""Add management users and revocable web sessions.

Revision ID: 20260724_0001
Revises:
Create Date: 2026-07-24
"""

from alembic import op
import sqlalchemy as sa


revision = "20260724_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('admin', 'operator', 'viewer')",
            name="ck_app_users_role",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_app_users_username", "app_users", ["username"], unique=True)

    op.create_table(
        "app_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["app_users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_app_sessions_expires_at", "app_sessions", ["expires_at"])
    op.create_index("ix_app_sessions_token_hash", "app_sessions", ["token_hash"], unique=True)
    op.create_index("ix_app_sessions_user_id", "app_sessions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_app_sessions_user_id", table_name="app_sessions")
    op.drop_index("ix_app_sessions_token_hash", table_name="app_sessions")
    op.drop_index("ix_app_sessions_expires_at", table_name="app_sessions")
    op.drop_table("app_sessions")
    op.drop_index("ix_app_users_username", table_name="app_users")
    op.drop_table("app_users")
