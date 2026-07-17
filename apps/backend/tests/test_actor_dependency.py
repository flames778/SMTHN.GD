from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from lockdin_backend.api.dependencies import ActorDependency
from lockdin_backend.persistence.base import Base
from lockdin_backend.persistence.database import get_identity_db
from lockdin_backend.persistence.identity import IdentityRepository
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

app = FastAPI()


@app.get("/actor")
def read_actor(actor: ActorDependency) -> dict[str, str | None]:
    return {
        "user_id": actor.user_id,
        "device_id": actor.device_id,
        "session_id": actor.session_id,
    }


@pytest.fixture
def client_and_token() -> Generator[tuple[TestClient, str], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = Session(engine)
    issued = IdentityRepository(db).bootstrap_first_user(
        display_name="Owner",
        device_name="Workstation",
        platform="windows",
    )

    def override_identity_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_identity_db] = override_identity_db
    try:
        yield TestClient(app), issued.token
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_actor_dependency_rejects_missing_identity(
    client_and_token: tuple[TestClient, str],
) -> None:
    client, _ = client_and_token
    response = client.get("/actor")

    assert response.status_code == 401
    assert response.json()["detail"]["type"].endswith("actor-context-required")


def test_actor_dependency_resolves_context_from_session(
    client_and_token: tuple[TestClient, str],
) -> None:
    client, token = client_and_token
    response = client.get("/actor", headers={"X-Lockdin-Session-Token": token})

    assert response.status_code == 200
    assert response.json()["user_id"]
    assert response.json()["device_id"]
    assert response.json()["session_id"]


def test_actor_dependency_rejects_unknown_session(
    client_and_token: tuple[TestClient, str],
) -> None:
    client, _ = client_and_token
    response = client.get(
        "/actor",
        headers={"X-Lockdin-Session-Token": "not-a-valid-token"},
    )

    assert response.status_code == 401
