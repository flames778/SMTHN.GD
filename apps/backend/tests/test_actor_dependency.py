from fastapi import FastAPI
from fastapi.testclient import TestClient
from lockdin_backend.api.dependencies import ActorDependency

app = FastAPI()


@app.get("/actor")
def read_actor(actor: ActorDependency) -> dict[str, str | None]:
    return {
        "user_id": actor.user_id,
        "device_id": actor.device_id,
        "session_id": actor.session_id,
    }


client = TestClient(app)


def test_actor_dependency_rejects_missing_identity() -> None:
    response = client.get("/actor")

    assert response.status_code == 401
    assert response.json()["detail"]["type"].endswith("actor-context-required")


def test_actor_dependency_builds_context_from_headers() -> None:
    response = client.get(
        "/actor",
        headers={
            "X-Lockdin-User-Id": "user-123",
            "X-Lockdin-Device-Id": "device-7",
            "X-Lockdin-Session-Id": "session-4",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "user_id": "user-123",
        "device_id": "device-7",
        "session_id": "session-4",
    }
