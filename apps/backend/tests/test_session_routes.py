from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from lockdin_backend.api.session_routes import router
from lockdin_backend.persistence.base import Base
from lockdin_backend.persistence.database import get_identity_db
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

app = FastAPI()
app.include_router(router)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("APP_BOOTSTRAP_TOKEN", "bootstrap-secret-with-at-least-32-chars")
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = Session(engine)

    def override_identity_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_identity_db] = override_identity_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        db.close()


def bootstrap_payload() -> dict[str, str]:
    return {
        "display_name": "Owner",
        "device_name": "Workstation",
        "platform": "windows",
    }


def test_bootstrap_rejects_invalid_setup_secret(client: TestClient) -> None:
    response = client.post(
        "/api/session/bootstrap",
        json=bootstrap_payload(),
        headers={"X-Lockdin-Bootstrap-Token": "wrong"},
    )

    assert response.status_code == 403


def test_bootstrap_issues_first_session_once(client: TestClient) -> None:
    headers = {"X-Lockdin-Bootstrap-Token": "bootstrap-secret-with-at-least-32-chars"}
    response = client.post("/api/session/bootstrap", json=bootstrap_payload(), headers=headers)

    assert response.status_code == 201
    assert response.json()["session_token"]
    assert response.json()["user_id"]
    assert response.json()["device_id"]

    repeated = client.post("/api/session/bootstrap", json=bootstrap_payload(), headers=headers)
    assert repeated.status_code == 409
