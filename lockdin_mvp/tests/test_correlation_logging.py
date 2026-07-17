"""Tests for structured correlation logging.

Validates correlation ID generation, propagation, and integration with
error responses and structured logging.
"""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from app.core.logging import (
    CorrelationIdMiddleware,
    StructuredLogger,
    get_correlation_id,
    set_actor_context,
    get_actor_context,
)
from app.api.problem_details_handlers import register_problem_details_handlers


class TestCorrelationIdMiddleware:
    """Test correlation ID middleware."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app with middleware."""
        app = FastAPI()
        app.add_middleware(CorrelationIdMiddleware)
        register_problem_details_handlers(app)

        @app.get("/test")
        def test_endpoint() -> dict[str, str]:
            return {"correlation_id": get_correlation_id()}

        @app.get("/error")
        def error_endpoint() -> None:
            raise HTTPException(status_code=400, detail="Bad request")

        return app

    def test_correlation_id_generation(self, app):
        """Test that correlation ID is generated if not provided."""
        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        data = response.json()
        assert data["correlation_id"]
        assert len(data["correlation_id"]) > 0
        # Check that response header contains correlation_id
        assert "X-Correlation-ID" in response.headers
        assert response.headers["X-Correlation-ID"] == data["correlation_id"]

    def test_correlation_id_extraction(self, app):
        """Test that provided correlation ID is extracted."""
        client = TestClient(app)
        custom_id = str(uuid.uuid4())
        response = client.get("/test", headers={"X-Correlation-ID": custom_id})

        assert response.status_code == 200
        data = response.json()
        assert data["correlation_id"] == custom_id
        assert response.headers["X-Correlation-ID"] == custom_id

    def test_correlation_id_in_error_response(self, app):
        """Test that correlation_id is included in error responses."""
        client = TestClient(app)
        custom_id = str(uuid.uuid4())
        response = client.get("/error", headers={"X-Correlation-ID": custom_id})

        assert response.status_code == 400
        data = response.json()
        assert data["correlation_id"] == custom_id
        assert data["error_code"] == "BAD_REQUEST"

    def test_correlation_id_response_header(self, app):
        """Test that correlation ID is included in response headers."""
        client = TestClient(app)
        custom_id = str(uuid.uuid4())
        response = client.get("/test", headers={"X-Correlation-ID": custom_id})

        assert response.headers["X-Correlation-ID"] == custom_id


class TestStructuredLogger:
    """Test structured JSON logging."""

    @pytest.fixture(autouse=True)
    def reset_context(self):
        """Reset context variables before each test."""
        from app.core.logging import _correlation_id, _user_id, _device_id

        _correlation_id.set("")
        _user_id.set("")
        _device_id.set("")
        yield
        _correlation_id.set("")
        _user_id.set("")
        _device_id.set("")

    def test_structured_logger_format(self, caplog):
        """Test that logger outputs valid JSON with correlation context."""
        from app.core.logging import _correlation_id, _user_id, _device_id

        _correlation_id.set("test-correlation-123")
        _user_id.set("user-456")
        _device_id.set("device-789")

        logger = StructuredLogger(__name__)
        logger.info("Test message", extra_field="extra_value")

        # caplog captures the log records
        assert len(caplog.records) > 0
        log_record = caplog.records[-1]
        log_data = json.loads(log_record.message)

        assert log_data["message"] == "Test message"
        assert log_data["level"] == "INFO"
        assert log_data["correlation_id"] == "test-correlation-123"
        assert log_data["user_id"] == "user-456"
        assert log_data["device_id"] == "device-789"
        assert log_data["extra_field"] == "extra_value"
        assert "timestamp" in log_data

    def test_structured_logger_error_level(self, caplog):
        """Test error level logging."""
        from app.core.logging import _correlation_id

        _correlation_id.set("error-test-123")

        logger = StructuredLogger(__name__)
        logger.error("Error message", error_code="TEST_ERROR")

        assert len(caplog.records) > 0
        log_record = caplog.records[-1]
        log_data = json.loads(log_record.message)

        assert log_data["message"] == "Error message"
        assert log_data["level"] == "ERROR"
        assert log_data["correlation_id"] == "error-test-123"
        assert log_data["error_code"] == "TEST_ERROR"

    def test_structured_logger_includes_timestamp(self, caplog):
        """Test that timestamp is included in logs."""
        from app.core.logging import _correlation_id

        _correlation_id.set("timestamp-test")

        logger = StructuredLogger(__name__)
        logger.info("Test message")

        assert len(caplog.records) > 0
        log_record = caplog.records[-1]
        log_data = json.loads(log_record.message)

        assert "timestamp" in log_data
        # Timestamp should be ISO format with Z suffix
        assert log_data["timestamp"].endswith("Z")


class TestActorContext:
    """Test actor context storage and retrieval."""

    @pytest.fixture(autouse=True)
    def reset_context(self):
        """Reset context variables before each test."""
        from app.core.logging import _correlation_id, _user_id, _device_id

        _correlation_id.set("")
        _user_id.set("")
        _device_id.set("")
        yield
        _correlation_id.set("")
        _user_id.set("")
        _device_id.set("")

    def test_set_and_get_actor_context(self):
        """Test setting and retrieving actor identity."""
        set_actor_context(user_id="user-123", device_id="device-456")

        context = get_actor_context()
        assert context["user_id"] == "user-123"
        assert context["device_id"] == "device-456"

    def test_partial_actor_context(self):
        """Test setting only some actor fields."""
        set_actor_context(user_id="user-789")

        context = get_actor_context()
        assert context["user_id"] == "user-789"
        # device_id should be empty string
        assert context["device_id"] == ""

    def test_actor_context_in_structured_logs(self, caplog):
        """Test that actor context appears in logs."""
        from app.core.logging import _correlation_id

        _correlation_id.set("actor-test-123")
        set_actor_context(user_id="user-abc", device_id="device-xyz")

        logger = StructuredLogger(__name__)
        logger.info("User action")

        assert len(caplog.records) > 0
        log_record = caplog.records[-1]
        log_data = json.loads(log_record.message)

        assert log_data["user_id"] == "user-abc"
        assert log_data["device_id"] == "device-xyz"


class TestCorrelationLoggingIntegration:
    """Test integration of correlation logging with FastAPI."""

    @pytest.fixture
    def app(self):
        """Create test app with full logging integration."""
        app = FastAPI()
        app.add_middleware(CorrelationIdMiddleware)
        register_problem_details_handlers(app)

        @app.get("/traced")
        def traced_endpoint() -> dict[str, str | dict]:
            """Endpoint that returns correlation ID."""
            return {
                "correlation_id": get_correlation_id(),
            }

        @app.get("/unauthorized")
        def unauthorized_endpoint() -> None:
            """Endpoint that requires authorization."""
            raise HTTPException(status_code=401, detail="Unauthorized")

        return app

    def test_correlation_id_flow_through_endpoints(self, app):
        """Test that correlation ID flows through middleware and endpoints."""
        client = TestClient(app)
        custom_id = "flow-test-" + str(uuid.uuid4())

        response = client.get("/traced", headers={"X-Correlation-ID": custom_id})

        assert response.status_code == 200
        data = response.json()
        assert data["correlation_id"] == custom_id

    def test_unauthorized_includes_correlation_id(self, app):
        """Test that authorization errors include correlation_id."""
        client = TestClient(app)
        custom_id = "auth-test-" + str(uuid.uuid4())

        response = client.get(
            "/unauthorized",
            headers={"X-Correlation-ID": custom_id}
        )

        assert response.status_code == 401
        data = response.json()
        assert data["correlation_id"] == custom_id
        assert data["error_code"] == "UNAUTHORIZED"

    def test_correlation_id_generates_if_missing(self, app):
        """Test that a correlation ID is generated if not provided."""
        client = TestClient(app)

        response1 = client.get("/traced")
        response2 = client.get("/traced")

        data1 = response1.json()
        data2 = response2.json()

        # Both should have correlation IDs
        assert data1["correlation_id"]
        assert data2["correlation_id"]
        # But they should be different (not reused)
        assert data1["correlation_id"] != data2["correlation_id"]
