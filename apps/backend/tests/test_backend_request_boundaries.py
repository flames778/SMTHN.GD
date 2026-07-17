"""Tests for backend request boundary protections."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.testclient import TestClient

from lockdin_backend.security.cors import get_cors_config
from lockdin_backend.security.request_boundaries import (
    RateLimitMiddleware,
    RateLimiter,
    RequestSizeLimitMiddleware,
)


class TestBackendRateLimiter:
    """Test backend RateLimiter utility class."""

    def test_rate_limiter_allows_requests_under_limit(self) -> None:
        """Test that requests under limit are allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        for i in range(5):
            assert limiter.is_allowed("user-id-123") is True

    def test_rate_limiter_rejects_requests_over_limit(self) -> None:
        """Test that requests over limit are rejected."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        for i in range(3):
            assert limiter.is_allowed("user-id-123") is True

        assert limiter.is_allowed("user-id-123") is False

    def test_rate_limiter_separate_keys(self) -> None:
        """Test that different keys have separate limits."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        assert limiter.is_allowed("user-1") is True
        assert limiter.is_allowed("user-1") is True
        assert limiter.is_allowed("user-1") is False

        assert limiter.is_allowed("user-2") is True
        assert limiter.is_allowed("user-2") is True
        assert limiter.is_allowed("user-2") is False


class TestBackendRateLimitMiddleware:
    """Test backend RateLimitMiddleware."""

    def test_rate_limit_middleware_allows_under_limit(self) -> None:
        """Test that requests under limit pass through."""
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, max_requests=5, window_seconds=60)

        @app.get("/test")
        def test_endpoint() -> dict:
            return {"status": "ok"}

        client = TestClient(app)

        for i in range(5):
            response = client.get("/test")
            assert response.status_code == 200

    def test_rate_limit_middleware_rejects_over_limit(self) -> None:
        """Test that requests over limit get 429."""
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, max_requests=2, window_seconds=60)

        @app.get("/test")
        def test_endpoint() -> dict:
            return {"status": "ok"}

        client = TestClient(app)

        assert client.get("/test").status_code == 200
        assert client.get("/test").status_code == 200

        response = client.get("/test")
        assert response.status_code == 429
        assert response.json()["error_code"] == "RATE_LIMIT_EXCEEDED"

    def test_rate_limit_middleware_uses_user_id_header(self) -> None:
        """Test that middleware respects x-user-id header."""
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, max_requests=2, window_seconds=60)

        @app.get("/test")
        def test_endpoint() -> dict:
            return {"status": "ok"}

        client = TestClient(app)

        # First user hits limit
        assert client.get("/test", headers={"x-user-id": "user-1"}).status_code == 200
        assert client.get("/test", headers={"x-user-id": "user-1"}).status_code == 200
        assert client.get("/test", headers={"x-user-id": "user-1"}).status_code == 429

        # Second user still has allowance
        assert client.get("/test", headers={"x-user-id": "user-2"}).status_code == 200
        assert client.get("/test", headers={"x-user-id": "user-2"}).status_code == 200


class TestBackendRequestSizeLimitMiddleware:
    """Test backend RequestSizeLimitMiddleware."""

    def test_request_size_limit_allows_small_requests(self) -> None:
        """Test that small requests are allowed."""
        app = FastAPI()
        app.add_middleware(RequestSizeLimitMiddleware, max_size_bytes=1000)

        @app.post("/test")
        def test_endpoint(data: dict) -> dict:
            return {"status": "ok"}

        client = TestClient(app)

        response = client.post(
            "/test",
            json={"message": "small"},
            headers={"Content-Length": "50"},
        )
        assert response.status_code == 200

    def test_request_size_limit_rejects_large_requests(self) -> None:
        """Test that large requests are rejected with 413."""
        app = FastAPI()
        app.add_middleware(RequestSizeLimitMiddleware, max_size_bytes=100)

        @app.post("/test")
        def test_endpoint(data: dict) -> dict:
            return {"status": "ok"}

        client = TestClient(app)

        response = client.post(
            "/test",
            json={"message": "x" * 1000},
            headers={"Content-Length": "1000"},
        )
        assert response.status_code == 413
        assert response.json()["error_code"] == "REQUEST_TOO_LARGE"


class TestBackendCORSConfiguration:
    """Test backend CORS configuration."""

    def test_cors_config_development(self) -> None:
        """Test CORS config for development."""
        config = get_cors_config("development")

        assert "http://localhost:3000" in config["allow_origins"]
        assert config["allow_credentials"] is True

    def test_cors_config_staging(self) -> None:
        """Test CORS config for staging."""
        config = get_cors_config("staging")

        assert "https://app-staging.lockdin.ai" in config["allow_origins"]
        assert config["allow_credentials"] is True

    def test_cors_config_production(self) -> None:
        """Test CORS config for production."""
        config = get_cors_config("production")

        assert "https://app.lockdin.ai" in config["allow_origins"]
        assert "http://" not in str(config["allow_origins"])


class TestCORSIntegration:
    """Test CORS middleware integration with backend."""

    def test_cors_middleware_handles_preflight(self) -> None:
        """Test that CORS preflight requests are handled."""
        app = FastAPI()
        cors_config = get_cors_config("development")
        app.add_middleware(CORSMiddleware, **cors_config)

        @app.get("/test")
        def test_endpoint() -> dict:
            return {"status": "ok"}

        client = TestClient(app)

        response = client.options(
            "/test",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
