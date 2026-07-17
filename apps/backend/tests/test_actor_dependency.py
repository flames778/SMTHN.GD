from collections.abc import Generator

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import JSONResponse
from lockdin_backend.api.dependencies import ActorDependency
from lockdin_backend.domain.problem_details import ProblemDetails
from lockdin_backend.persistence.base import Base
from lockdin_backend.persistence.database import get_identity_db
from lockdin_backend.persistence.identity import IdentityRepository
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

app = FastAPI()


# Add problem details exception handler
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Convert HTTPException to RFC 9457 Problem Details."""
    if isinstance(exc.detail, dict) and "error_code" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )
    
    # Map status codes to error codes
    status_to_error_code = {
        status.HTTP_400_BAD_REQUEST: ("BAD_REQUEST", "Bad Request"),
        status.HTTP_401_UNAUTHORIZED: ("UNAUTHORIZED", "Unauthorized"),
        status.HTTP_403_FORBIDDEN: ("FORBIDDEN", "Forbidden"),
        status.HTTP_404_NOT_FOUND: ("NOT_FOUND", "Not Found"),
        status.HTTP_409_CONFLICT: ("CONFLICT", "Conflict"),
        status.HTTP_500_INTERNAL_SERVER_ERROR: ("INTERNAL_SERVER_ERROR", "Internal Server Error"),
        status.HTTP_503_SERVICE_UNAVAILABLE: ("SERVICE_UNAVAILABLE", "Service Unavailable"),
    }
    
    error_code, title = status_to_error_code.get(
        exc.status_code, ("UNKNOWN_ERROR", "Unknown Error")
    )
    
    details = ProblemDetails(
        type=f"https://api.lockdin.ai/errors/{error_code.lower().replace('_', '-')}",
        status=exc.status_code,
        title=title,
        detail=str(exc.detail) if exc.detail else None,
        error_code=error_code,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=details.to_dict(),
    )


app.add_exception_handler(HTTPException, http_exception_handler)


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
    data = response.json()
    assert data["error_code"] == "UNAUTHORIZED"
    assert "unauthorized" in data["type"]


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
