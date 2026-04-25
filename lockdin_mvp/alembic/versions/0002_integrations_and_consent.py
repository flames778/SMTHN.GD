"""add integrations and consent tables

Revision ID: 0002_integrations_and_consent
Revises: 0001_initial
Create Date: 2026-04-25 00:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_integrations_and_consent"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "integration_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("token_type", sa.String(length=32), nullable=False, server_default="Bearer"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="connected"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_integration_tokens_user_id", "integration_tokens", ["user_id"], unique=False)
    op.create_index("ix_integration_tokens_provider", "integration_tokens", ["provider"], unique=False)

    op.create_table(
        "consent_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("integration", sa.String(length=32), nullable=False),
        sa.Column("data_category", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=128), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_consent_records_user_id", "consent_records", ["user_id"], unique=False)
    op.create_index("ix_consent_records_integration", "consent_records", ["integration"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_consent_records_integration", table_name="consent_records")
    op.drop_index("ix_consent_records_user_id", table_name="consent_records")
    op.drop_table("consent_records")

    op.drop_index("ix_integration_tokens_provider", table_name="integration_tokens")
    op.drop_index("ix_integration_tokens_user_id", table_name="integration_tokens")
    op.drop_table("integration_tokens")
