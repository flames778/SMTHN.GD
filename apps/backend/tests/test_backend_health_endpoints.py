"""Tests for backend health, readiness, dependency, and version endpoints."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from lockdin_backend.api.health import (
    DependencyStatus,
    _check_identity_db,
    router,
)


@pytest.fixture
def health_client() -> TestClient:
    """Create a TestClient with only the health router."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestBackendHealthEndpoint:
    """Test backend /health liveness probe."""

    def test_health_returns_200(self, health_client: TestClient) -> None:
        """Test that /health returns 200."""
        response = health_client.get("/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self, health_client: TestClient) -> None:
        """Test that /health body is {"status": "ok"}."""
        response = health_client.get("/health")
        assert response.json() == {"status": "ok"}


class TestBackendReadinessEndpoint:
    """Test backend /ready readiness probe."""

    def test_readiness_returns_200_when_db_healthy(
        self, health_client: TestClient
    ) -> None:
        """Test /ready returns 200 with healthy database."""
        healthy_db = DependencyStatus(name="identity_database", status="ok", latency_ms=1.0)

        with patch("lockdin_backend.api.health._check_identity_db", return_value=healthy_db):
            response = health_client.get("/ready")

        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    def test_readiness_returns_503_when_db_down(
        self, health_client: TestClient
    ) -> None:
        """Test /ready returns 503 when database is down."""
        down_db = DependencyStatus(
            name="identity_database", status="down", detail="No connection"
        )

        with patch("lockdin_backend.api.health._check_identity_db", return_value=down_db):
            response = health_client.get("/ready")

        assert response.status_code == 503
        assert response.json()["status"] == "not_ready"

    def test_readiness_includes_dependency_details(
        self, health_client: TestClient
    ) -> None:
        """Test /ready includes dependency details in response."""
        healthy_db = DependencyStatus(name="identity_database", status="ok", latency_ms=3.7)

        with patch("lockdin_backend.api.health._check_identity_db", return_value=healthy_db):
            response = health_client.get("/ready")

        data = response.json()
        deps = data["dependencies"]
        assert len(deps) == 1
        assert deps[0]["name"] == "identity_database"


class TestBackendDependenciesEndpoint:
    """Test backend /dependencies probe."""

    def test_dependencies_always_returns_200(
        self, health_client: TestClient
    ) -> None:
        """Test /dependencies always returns 200 even with failures."""
        down_db = DependencyStatus(name="identity_database", status="down")

        with patch("lockdin_backend.api.health._check_identity_db", return_value=down_db):
            response = health_client.get("/dependencies")

        assert response.status_code == 200

    def test_dependencies_returns_list(self, health_client: TestClient) -> None:
        """Test /dependencies returns list in dependencies key."""
        ok_db = DependencyStatus(name="identity_database", status="ok", latency_ms=1.0)

        with patch("lockdin_backend.api.health._check_identity_db", return_value=ok_db):
            response = health_client.get("/dependencies")

        data = response.json()
        assert isinstance(data["dependencies"], list)


class TestBackendVersionEndpoint:
    """Test backend /version endpoint."""

    def test_version_returns_200(self, health_client: TestClient) -> None:
        """Test /version returns 200."""
        response = health_client.get("/version")
        assert response.status_code == 200

    def test_version_includes_required_fields(self, health_client: TestClient) -> None:
        """Test /version includes version, environment, uptime_seconds."""
        response = health_client.get("/version")
        data = response.json()
        assert "version" in data
        assert "environment" in data
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0
