"""add password_reset_tokens table

Revision ID: 003
Revises: 393e6319018d
Create Date: 2026-02-21
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "003"
down_revision = "393e6319018d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id",         sa.String(36),  primary_key=True, nullable=False),
        sa.Column("user_id",    sa.String(36),  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token",      sa.String(128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prt_user_id", "password_reset_tokens", ["user_id"])
    op.create_index("ix_prt_token",   "password_reset_tokens", ["token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_prt_token",   table_name="password_reset_tokens")
    op.drop_index("ix_prt_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
