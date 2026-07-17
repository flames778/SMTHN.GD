"""Pytest configuration and fixtures for MVP integration tests.

Provides database fixtures, factory functions for test data, and FastAPI TestClient.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base as MVPBase
from app.db.session import get_db
from app.main import app
from lockdin_backend.persistence.base import Base as IdentityBase
from lockdin_backend.persistence.database import get_identity_db
from lockdin_backend.persistence.identity import IdentityRepository


@pytest.fixture
def mvp_engine():
    """Create in-memory SQLite engine for MVP tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    MVPBase.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def identity_engine():
    """Create in-memory SQLite engine for identity/backend tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    IdentityBase.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def mvp_db(mvp_engine) -> Generator[Session, None, None]:
    """Provide MVP database session for tests."""
    Session_local = sessionmaker(bind=mvp_engine, expire_on_commit=False)
    db = Session_local()
    yield db
    db.close()


@pytest.fixture
def identity_db(identity_engine) -> Generator[Session, None, None]:
    """Provide identity database session for tests."""
    Session_local = sessionmaker(bind=identity_engine, expire_on_commit=False)
    db = Session_local()
    yield db
    db.close()


@pytest.fixture
def client_with_db(mvp_db, identity_db) -> Generator[TestClient, None, None]:
    """Provide FastAPI TestClient with database overrides."""

    def override_get_db() -> Generator[Session, None, None]:
        yield mvp_db

    def override_get_identity_db() -> Generator[Session, None, None]:
        yield identity_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_identity_db] = override_get_identity_db

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def issued_owner(identity_db: Session) -> dict[str, str]:
    """Create a bootstrapped owner user with session token.

    Returns:
        Dict with user_id, device_id, session_id, and token.
    """
    issued = IdentityRepository(identity_db).bootstrap_first_user(
        display_name="Test Owner",
        device_name="Test Device",
        platform="test",
    )

    return {
        "user_id": issued.user_id,
        "device_id": issued.device_id,
        "session_id": issued.session_id,
        "token": issued.token,
    }


@pytest.fixture
def auth_headers(issued_owner: dict[str, str]) -> dict[str, str]:
    """Provide authorization headers for authenticated requests.

    Returns:
        Dict with X-Lockdin-Session-Token header.
    """
    return {"X-Lockdin-Session-Token": issued_owner["token"]}
