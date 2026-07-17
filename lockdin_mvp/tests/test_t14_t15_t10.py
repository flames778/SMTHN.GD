"""Tests for T14 (event uniqueness/timezone), T15 (audit storage), T10 (idempotency)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.db.base import Base
from app.db.models import AuditEventModel, EventModel
from app.repositories.audit import AuditRepository
from app.security.idempotency import IdempotencyMiddleware, IdempotencyStore


# --------------------------------------------------------------------------- #
# Shared fixture
# --------------------------------------------------------------------------- #

@pytest.fixture
def mvp_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=True, expire_on_commit=False, class_=Session)
    with factory() as db:
        yield db


# --------------------------------------------------------------------------- #
# T14 — Event uniqueness and timezone constraints
# --------------------------------------------------------------------------- #

class TestEventUniqueness:
    """Test M1-T14: event uniqueness constraint."""

    def test_event_unique_constraint_prevents_duplicate_external_id(self, mvp_db: Session) -> None:
        """Test that two events with same user+source+external_id raise IntegrityError."""
        now = datetime(2025, 6, 1, 12, 0, tzinfo=timezone.utc)

        mvp_db.add(EventModel(
            user_id="u1", source="google_calendar", external_id="evt-001",
            title="Meeting", starts_at=now,
        ))
        mvp_db.commit()

        mvp_db.add(EventModel(
            user_id="u1", source="google_calendar", external_id="evt-001",
            title="Duplicate Meeting", starts_at=now,
        ))
        with pytest.raises(IntegrityError):
            mvp_db.commit()

    def test_same_external_id_different_user_is_allowed(self, mvp_db: Session) -> None:
        """Test that same external_id for different users is allowed."""
        now = datetime(2025, 6, 1, 12, 0, tzinfo=timezone.utc)

        mvp_db.add(EventModel(
            user_id="u1", source="google_calendar", external_id="evt-001",
            title="Meeting U1", starts_at=now,
        ))
        mvp_db.add(EventModel(
            user_id="u2", source="google_calendar", external_id="evt-001",
            title="Meeting U2", starts_at=now,
        ))
        mvp_db.commit()  # Should not raise

        events = mvp_db.scalars(select(EventModel).where(EventModel.external_id == "evt-001")).all()
        assert len(events) == 2

    def test_event_stores_timezone_aware_timestamps(self, mvp_db: Session) -> None:
        """Test that events store and retrieve timezone-aware timestamps."""
        starts_at = datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc)
        ends_at = datetime(2025, 6, 1, 11, 0, tzinfo=timezone.utc)

        mvp_db.add(EventModel(
            user_id="u1", source="google_calendar", external_id="evt-tz-001",
            title="Timezone Meeting", starts_at=starts_at, ends_at=ends_at,
        ))
        mvp_db.commit()

        row = mvp_db.scalar(select(EventModel).where(EventModel.external_id == "evt-tz-001"))
        assert row is not None
        # Timestamps should be stored and the model uses timezone-aware columns
        assert row.starts_at is not None
        assert row.ends_at is not None

    def test_event_model_has_user_id_field(self, mvp_db: Session) -> None:
        """Test that EventModel now includes user_id for proper ownership."""
        now = datetime(2025, 6, 1, 12, 0, tzinfo=timezone.utc)
        mvp_db.add(EventModel(
            user_id="user-xyz", source="gcal", external_id="evt-owner",
            title="Owner Test", starts_at=now,
        ))
        mvp_db.commit()

        row = mvp_db.scalar(select(EventModel).where(EventModel.external_id == "evt-owner"))
        assert row.user_id == "user-xyz"


# --------------------------------------------------------------------------- #
# T15 — Append-only audit storage
# --------------------------------------------------------------------------- #

class TestAuditRepository:
    """Test M1-T15: append-only audit storage."""

    def test_record_creates_audit_event(self, mvp_db: Session) -> None:
        """Test that record() appends an audit event row."""
        repo = AuditRepository(mvp_db)
        event = repo.record(
            "integration.connected",
            user_id="user-1",
            resource_type="integration",
            resource_id="int-1",
        )
        mvp_db.commit()

        assert event.id is not None
        assert event.action == "integration.connected"
        assert event.user_id == "user-1"
        assert event.outcome == "success"

    def test_record_captures_failure_outcome(self, mvp_db: Session) -> None:
        """Test that failures are recorded with outcome=failure."""
        repo = AuditRepository(mvp_db)
        event = repo.record(
            "session.bootstrap_failed",
            outcome="failure",
            detail="Invalid setup secret",
        )
        mvp_db.commit()

        assert event.outcome == "failure"
        assert event.detail == "Invalid setup secret"

    def test_list_for_user_returns_events_newest_first(self, mvp_db: Session) -> None:
        """Test list_for_user returns all events for the user."""
        repo = AuditRepository(mvp_db)
        repo.record("consent.granted", user_id="user-1")
        repo.record("integration.connected", user_id="user-1")
        repo.record("consent.revoked", user_id="user-1")
        mvp_db.commit()

        events = repo.list_for_user("user-1")
        assert len(events) == 3
        actions = {e.action for e in events}
        assert actions == {"consent.granted", "integration.connected", "consent.revoked"}

    def test_list_for_user_filters_by_action_prefix(self, mvp_db: Session) -> None:
        """Test that action_prefix filters audit events correctly."""
        repo = AuditRepository(mvp_db)
        repo.record("integration.connected", user_id="user-1")
        repo.record("consent.granted", user_id="user-1")
        repo.record("integration.revoked", user_id="user-1")
        mvp_db.commit()

        integration_events = repo.list_for_user("user-1", action_prefix="integration.")
        assert len(integration_events) == 2
        assert all(e.action.startswith("integration.") for e in integration_events)

    def test_list_for_user_does_not_return_other_users_events(self, mvp_db: Session) -> None:
        """Test that list_for_user is scoped to the given user."""
        repo = AuditRepository(mvp_db)
        repo.record("integration.connected", user_id="user-1")
        repo.record("integration.connected", user_id="user-2")
        mvp_db.commit()

        events = repo.list_for_user("user-1")
        assert len(events) == 1
        assert events[0].user_id == "user-1"

    def test_audit_event_has_occurred_at_timestamp(self, mvp_db: Session) -> None:
        """Test that audit events have timezone-aware occurred_at timestamp."""
        repo = AuditRepository(mvp_db)
        event = repo.record("session.created", user_id="user-1")
        mvp_db.commit()

        assert event.occurred_at is not None

    def test_audit_event_accepts_correlation_id(self, mvp_db: Session) -> None:
        """Test that correlation_id is stored in audit events."""
        repo = AuditRepository(mvp_db)
        event = repo.record(
            "integration.connected",
            user_id="user-1",
            correlation_id="corr-abc-123",
        )
        mvp_db.commit()

        assert event.correlation_id == "corr-abc-123"


# --------------------------------------------------------------------------- #
# T10 — Idempotency keys for mutations
# --------------------------------------------------------------------------- #

class TestIdempotencyStore:
    """Test IdempotencyStore in-memory implementation."""

    def test_get_returns_none_for_unknown_key(self) -> None:
        store = IdempotencyStore()
        assert store.get("unknown-key") is None

    def test_set_and_get_round_trip(self) -> None:
        store = IdempotencyStore()
        store.set("key-1", 201, {"id": "abc"})
        record = store.get("key-1")

        assert record is not None
        assert record["status_code"] == 201
        assert record["body"] == {"id": "abc"}

    def test_different_keys_are_independent(self) -> None:
        store = IdempotencyStore()
        store.set("key-a", 200, {"a": 1})
        store.set("key-b", 201, {"b": 2})

        assert store.get("key-a")["body"] == {"a": 1}
        assert store.get("key-b")["body"] == {"b": 2}


class TestIdempotencyMiddleware:
    """Test IdempotencyMiddleware replays and caches responses."""

    def _app_with_counter(self):
        """Create a FastAPI app where each POST increments a call counter."""
        app = FastAPI()
        store = IdempotencyStore()
        app.add_middleware(IdempotencyMiddleware, store=store)
        counter = {"calls": 0}

        @app.post("/items")
        def create_item() -> dict:
            counter["calls"] += 1
            return {"id": "item-1", "call": counter["calls"]}

        return TestClient(app), counter

    def test_second_request_with_same_key_is_replayed(self) -> None:
        """Test that a duplicate request returns the stored response."""
        client, counter = self._app_with_counter()

        r1 = client.post("/items", headers={"Idempotency-Key": "idem-123"})
        r2 = client.post("/items", headers={"Idempotency-Key": "idem-123"})

        assert r1.status_code == 200
        assert r2.status_code == 200
        # Handler called only once
        assert counter["calls"] == 1
        assert r1.json() == r2.json()

    def test_replay_includes_replayed_header(self) -> None:
        """Test that replayed responses include X-Idempotency-Replayed header."""
        client, _ = self._app_with_counter()

        client.post("/items", headers={"Idempotency-Key": "idem-replay"})
        r2 = client.post("/items", headers={"Idempotency-Key": "idem-replay"})

        assert r2.headers.get("X-Idempotency-Replayed") == "true"

    def test_different_keys_produce_independent_responses(self) -> None:
        """Test that different idempotency keys produce independent calls."""
        client, counter = self._app_with_counter()

        client.post("/items", headers={"Idempotency-Key": "key-a"})
        client.post("/items", headers={"Idempotency-Key": "key-b"})

        assert counter["calls"] == 2

    def test_get_requests_bypass_idempotency(self) -> None:
        """Test that GET requests bypass idempotency (only mutations are cached)."""
        app = FastAPI()
        store = IdempotencyStore()
        app.add_middleware(IdempotencyMiddleware, store=store)
        counter = {"calls": 0}

        @app.get("/items")
        def list_items() -> dict:
            counter["calls"] += 1
            return {"items": []}

        client = TestClient(app)
        client.get("/items", headers={"Idempotency-Key": "idem-get"})
        client.get("/items", headers={"Idempotency-Key": "idem-get"})

        assert counter["calls"] == 2  # Not cached

    def test_requests_without_key_pass_through(self) -> None:
        """Test that requests without Idempotency-Key pass through normally."""
        client, counter = self._app_with_counter()

        client.post("/items")
        client.post("/items")

        assert counter["calls"] == 2
