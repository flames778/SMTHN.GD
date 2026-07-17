from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EventModel(Base):
    __tablename__ = "events"
    __table_args__ = (
        # Uniqueness: one canonical record per source + external_id per user
        UniqueConstraint("user_id", "source", "external_id", name="uq_event_user_source_external"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(255))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    meeting_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)


class TaskSuggestionModel(Base):
    __tablename__ = "task_suggestions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    event_id: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(255))
    reason: Mapped[str] = mapped_column(Text)
    urgency: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


class IntegrationTokenModel(Base):
    __tablename__ = "integration_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str] = mapped_column(Text)
    scope: Mapped[str] = mapped_column(Text)
    token_type: Mapped[str] = mapped_column(String(32), default="Bearer")
    status: Mapped[str] = mapped_column(String(32), default="connected")
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)


class ConsentRecordModel(Base):
    __tablename__ = "consent_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    integration: Mapped[str] = mapped_column(String(32), index=True)
    data_category: Mapped[str] = mapped_column(String(64))
    purpose: Mapped[str] = mapped_column(String(128))
    granted: Mapped[bool] = mapped_column(Boolean)
    granted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)


class AuditEventModel(Base):
    """Append-only audit log — rows are never updated or deleted.

    Records every security-relevant mutation with enough context for forensic replay.
    """

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    # Who performed the action
    user_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    # What happened
    action: Mapped[str] = mapped_column(String(128), index=True)  # e.g. "integration.connected"
    resource_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # e.g. "integration"
    resource_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    # Observability
    correlation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    outcome: Mapped[str] = mapped_column(String(32), default="success")  # success | failure
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Immutable timestamp — never updated
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, index=True)
