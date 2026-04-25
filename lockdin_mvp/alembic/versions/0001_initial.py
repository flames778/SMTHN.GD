"""initial tables for events and reminders

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-25 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meeting_url", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_events_source", "events", ["source"], unique=False)
    op.create_index("ix_events_external_id", "events", ["external_id"], unique=False)
    op.create_index("ix_events_starts_at", "events", ["starts_at"], unique=False)

    op.create_table(
        "task_suggestions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("urgency", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_task_suggestions_event_id", "task_suggestions", ["event_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_task_suggestions_event_id", table_name="task_suggestions")
    op.drop_table("task_suggestions")

    op.drop_index("ix_events_starts_at", table_name="events")
    op.drop_index("ix_events_external_id", table_name="events")
    op.drop_index("ix_events_source", table_name="events")
    op.drop_table("events")
