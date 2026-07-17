"""Append-only audit event repository.

Audit events are write-once: no updates, no deletes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_correlation_id
from app.db.models import AuditEventModel


class AuditRepository:
    """Write-only repository for audit events.

    All methods append new rows; existing rows are never touched.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def record(
        self,
        action: str,
        *,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        outcome: str = "success",
        detail: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> AuditEventModel:
        """Append one audit event. Caller owns the commit.

        Args:
            action: Dot-namespaced action label, e.g. "integration.connected".
            user_id: Acting user (None for unauthenticated events).
            session_id: Acting session (None if not yet authenticated).
            resource_type: Type of resource affected, e.g. "integration".
            resource_id: ID of the affected resource.
            outcome: "success" or "failure".
            detail: Optional freeform context string.
            correlation_id: Request correlation ID (auto-read from context if None).
        """
        event = AuditEventModel(
            user_id=user_id,
            session_id=session_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id or get_correlation_id(),
            outcome=outcome,
            detail=detail,
        )
        self._db.add(event)
        self._db.flush()
        return event

    def list_for_user(
        self,
        user_id: str,
        *,
        limit: int = 100,
        action_prefix: Optional[str] = None,
    ) -> list[AuditEventModel]:
        """List audit events for a user, newest first.

        Args:
            user_id: User to query.
            limit: Maximum number of events to return.
            action_prefix: Optional filter prefix, e.g. "integration.".
        """
        q = select(AuditEventModel).where(AuditEventModel.user_id == user_id)
        if action_prefix:
            q = q.where(AuditEventModel.action.startswith(action_prefix))
        q = q.order_by(AuditEventModel.occurred_at.desc()).limit(limit)
        return list(self._db.scalars(q).all())
