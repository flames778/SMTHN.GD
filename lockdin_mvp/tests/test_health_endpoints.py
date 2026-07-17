"""Tests for health, readiness, dependency, and version endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.api.health import (
    DependencyStatus,
    HealthResponse,
    VersionResponse,
    _check_database,
    router,
)


@pytest.fixture
def health_client() -> TestClient:
    """Create a TestClient with only the health router."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestHealthEndpoint:
    """Test /health liveness probe."""

    def test_health_returns_200(self, health_client: TestClient) -> None:
        """Test that /health returns 200 OK."""
        response = health_client.get("/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self, health_client: TestClient) -> None:
        """Test that /health returns {"status": "ok"}."""
        response = health_client.get("/health")
        assert response.json() == {"status": "ok"}

    def test_health_no_auth_required(self, health_client: TestClient) -> None:
        """Test that /health requires no authentication."""
        response = health_client.get("/health")
        assert response.status_code == 200


class TestReadinessEndpoint:
    """Test /ready readiness probe."""

    def test_readiness_structure_when_db_healthy(
        self, health_client: TestClient
    ) -> None:
        """Test /ready response structure with healthy database."""
        healthy_db = DependencyStatus(name="database", status="ok", latency_ms=1.2)

        with patch("app.api.health._check_database", return_value=healthy_db):
            response = health_client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert len(data["dependencies"]) == 1
        assert data["dependencies"][0]["name"] == "database"
        assert data["dependencies"][0]["status"] == "ok"

    def test_readiness_returns_503_when_db_down(
        self, health_client: TestClient
    ) -> None:
        """Test /ready returns 503 when database is unavailable."""
        down_db = DependencyStatus(
            name="database", status="down", latency_ms=0.0, detail="Connection refused"
        )

        with patch("app.api.health._check_database", return_value=down_db):
            response = health_client.get("/ready")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"

    def test_readiness_includes_latency(self, health_client: TestClient) -> None:
        """Test /ready includes latency in dependency status."""
        healthy_db = DependencyStatus(name="database", status="ok", latency_ms=5.5)

        with patch("app.api.health._check_database", return_value=healthy_db):
            response = health_client.get("/ready")

        data = response.json()
        assert "latency_ms" in data["dependencies"][0]
        assert data["dependencies"][0]["latency_ms"] == 5.5


class TestDependenciesEndpoint:
    """Test /dependencies probe."""

    def test_dependencies_always_returns_200(
        self, health_client: TestClient
    ) -> None:
        """Test /dependencies always returns 200 regardless of dependency health."""
        down_db = DependencyStatus(
            name="database", status="down", detail="Connection refused"
        )

        with patch("app.api.health._check_database", return_value=down_db):
            response = health_client.get("/dependencies")

        assert response.status_code == 200

    def test_dependencies_returns_all_statuses(
        self, health_client: TestClient
    ) -> None:
        """Test /dependencies returns status for all dependencies."""
        healthy_db = DependencyStatus(name="database", status="ok", latency_ms=2.1)

        with patch("app.api.health._check_database", return_value=healthy_db):
            response = health_client.get("/dependencies")

        data = response.json()
        assert "dependencies" in data
        assert len(data["dependencies"]) >= 1

    def test_dependencies_shows_degraded_status(
        self, health_client: TestClient
    ) -> None:
        """Test /dependencies can show degraded status."""
        degraded_db = DependencyStatus(
            name="database", status="degraded", latency_ms=900.0, detail="High latency"
        )

        with patch("app.api.health._check_database", return_value=degraded_db):
            response = health_client.get("/dependencies")

        data = response.json()
        assert data["dependencies"][0]["status"] == "degraded"
        assert data["dependencies"][0]["detail"] == "High latency"


class TestVersionEndpoint:
    """Test /version endpoint."""

    def test_version_returns_200(self, health_client: TestClient) -> None:
        """Test /version returns 200."""
        response = health_client.get("/version")
        assert response.status_code == 200

    def test_version_includes_version_field(self, health_client: TestClient) -> None:
        """Test /version includes version string."""
        response = health_client.get("/version")
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)

    def test_version_includes_environment(self, health_client: TestClient) -> None:
        """Test /version includes environment field."""
        response = health_client.get("/version")
        data = response.json()
        assert "environment" in data

    def test_version_includes_uptime(self, health_client: TestClient) -> None:
        """Test /version includes uptime_seconds."""
        response = health_client.get("/version")
        data = response.json()
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0


class TestDependencyStatusModel:
    """Test DependencyStatus model."""

    def test_dependency_status_ok(self) -> None:
        """Test DependencyStatus with ok status."""
        dep = DependencyStatus(name="db", status="ok", latency_ms=1.5)
        assert dep.name == "db"
        assert dep.status == "ok"
        assert dep.latency_ms == 1.5
        assert dep.detail is None

    def test_dependency_status_down_with_detail(self) -> None:
        """Test DependencyStatus with down status and detail."""
        dep = DependencyStatus(
            name="cache", status="down", detail="Connection timeout"
        )
        assert dep.status == "down"
        assert dep.detail == "Connection timeout"

    def test_dependency_status_excludes_none_on_dump(self) -> None:
        """Test that None fields are excluded from model dump."""
        dep = DependencyStatus(name="db", status="ok")
        dumped = dep.model_dump(exclude_none=True)
        assert "latency_ms" not in dumped
        assert "detail" not in dumped


class TestCheckDatabase:
    """Test database check helper."""

    def test_check_database_returns_ok_when_connected(self) -> None:
        """Test _check_database returns ok status on successful connection."""
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_db)
        mock_session.__exit__ = MagicMock(return_value=False)

        with patch("app.db.session.SessionLocal", return_value=mock_session):
            result = _check_database()

        assert result.status == "ok"
        assert result.name == "database"
        assert result.latency_ms is not None

    def test_check_database_returns_down_on_error(self) -> None:
        """Test _check_database returns down status on connection error."""
        with patch("app.db.session.SessionLocal", side_effect=Exception("No connection")):
            result = _check_database()

        assert result.status == "down"
        assert result.name == "database"
        assert result.detail is not None
