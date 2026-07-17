import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("path", ["/api/consent", "/api/integrations"])
def test_protected_routes_reject_missing_actor_context(path: str) -> None:
    response = client.get(path)

    assert response.status_code == 401
    assert response.json()["detail"]["type"].endswith("actor-context-required")