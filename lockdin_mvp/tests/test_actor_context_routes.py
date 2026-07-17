from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base as LegacyBase
from app.db.session import get_db
from app.main import app
from lockdin_backend.persistence.base import Base as IdentityBase
from lockdin_backend.persistence.database import get_identity_db
from lockdin_backend.persistence.identity import IdentityRepository

client = TestClient(app)


@pytest.mark.parametrize("path", ["/api/consent", "/api/integrations"])
def test_protected_routes_reject_missing_actor_context(path: str) -> None:
    response = client.get(path)

    assert response.status_code == 401
    data = response.json()
    assert data["error_code"] == "UNAUTHORIZED"
    assert "unauthorized" in data["type"]


def test_issued_session_authenticates_protected_consent_route() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    LegacyBase.metadata.create_all(engine)
    IdentityBase.metadata.create_all(engine)
    db = Session(engine)
    issued = IdentityRepository(db).bootstrap_first_user(
        display_name="Owner",
        device_name="Workstation",
        platform="windows",
    )

    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_identity_db] = override_db
    try:
        response = client.get(
            "/api/consent",
            headers={"X-Lockdin-Session-Token": issued.token},
        )
    finally:
        app.dependency_overrides.clear()
        db.close()

    assert response.status_code == 200
    assert response.json() == []