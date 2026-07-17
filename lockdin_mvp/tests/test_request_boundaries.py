"""Tests for request boundary protections: CORS, rate limiting, request size validation."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.testclient import TestClient

from app.security.cors import get_cors_config
from app.security.request_boundaries import (
    RateLimitMiddleware,
    RateLimiter,
    RequestSizeLimitMiddleware,
    TrustedHostMiddleware,
)


class TestRateLimiter:
    """Test RateLimiter utility class."""

    def test_rate_limiter_allows_requests_under_limit(self) -> None:
        """Test that requests under limit are allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        for i in range(5):
            assert limiter.is_allowed("user-1") is True

    def test_rate_limiter_rejects_requests_over_limit(self) -> None:
        """Test that requests over limit are rejected."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        # First 3 allowed
        for i in range(3):
            assert limiter.is_allowed("user-1") is True

        # 4th and beyond rejected
        assert limiter.is_allowed("user-1") is False
        assert limiter.is_allowed("user-1") is False

    def test_rate_limiter_tracks_different_keys_separately(self) -> None:
        """Test that different keys have separate limits."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        # user-1 hits limit
        assert limiter.is_allowed("user-1") is True
        assert limiter.is_allowed("user-1") is True
        assert limiter.is_allowed("user-1") is False

        # user-2 still has allowance
        assert limiter.is_allowed("user-2") is True
        assert limiter.is_allowed("user-2") is True
        assert limiter.is_allowed("user-2") is False

    def test_rate_limiter_get_reset_time(self) -> None:
        """Test that reset time is calculated correctly."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.is_allowed("user-1")

        reset_time = limiter.get_reset_time("user-1")
        assert reset_time is not None


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware."""

    def test_rate_limit_middleware_allows_requests_under_limit(self) -> None:
        """Test that requests under limit are allowed through middleware."""
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
        """Test that requests over limit are rejected with 429."""
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, max_requests=2, window_seconds=60)

        @app.get("/test")
        def test_endpoint() -> dict:
            return {"status": "ok"}

        client = TestClient(app)

        # First 2 succeed
        assert client.get("/test").status_code == 200
        assert client.get("/test").status_code == 200

        # 3rd is rate limited
        response = client.get("/test")
        assert response.status_code == 429
        assert response.json()["error_code"] == "RATE_LIMIT_EXCEEDED"

    def test_rate_limit_middleware_includes_retry_after_header(self) -> None:
        """Test that 429 response includes Retry-After header."""
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, max_requests=1, window_seconds=60)

        @app.get("/test")
        def test_endpoint() -> dict:
            return {"status": "ok"}

        client = TestClient(app)

        # Hit limit
        client.get("/test")
        response = client.get("/test")

        assert response.status_code == 429
        assert "Retry-After" in response.headers


class TestTrustedHostMiddleware:
    """Test TrustedHostMiddleware."""

    def test_trusted_host_middleware_allows_trusted_hosts(self) -> None:
        """Test that trusted hosts are allowed."""
        app = FastAPI()
        app.add_middleware(
            TrustedHostMiddleware,
            trusted_hosts=["localhost:8000", "api.example.com"],
        )

        @app.get("/test")
        def test_endpoint() -> dict:
            return {"status": "ok"}

        client = TestClient(app)

        # TestClient sends Host header
        response = client.get("/test", headers={"Host": "localhost:8000"})
        assert response.status_code == 200

    def test_trusted_host_middleware_rejects_untrusted_hosts(self) -> None:
        """Test that untrusted hosts are rejected with 403."""
        app = FastAPI()
        app.add_middleware(
            TrustedHostMiddleware,
            trusted_hosts=["localhost:8000"],
        )

        @app.get("/test")
        def test_endpoint() -> dict:
            return {"status": "ok"}

        client = TestClient(app)

        response = client.get("/test", headers={"Host": "untrusted.example.com"})
        assert response.status_code == 403
        assert response.json()["error_code"] == "UNTRUSTED_HOST"

    def test_trusted_host_middleware_case_insensitive(self) -> None:
        """Test that host matching is case-insensitive."""
        app = FastAPI()
        app.add_middleware(
            TrustedHostMiddleware,
            trusted_hosts=["localhost:8000"],
        )

        @app.get("/test")
        def test_endpoint() -> dict:
            return {"status": "ok"}

        client = TestClient(app)

        response = client.get("/test", headers={"Host": "LOCALHOST:8000"})
        assert response.status_code == 200


class TestRequestSizeLimitMiddleware:
    """Test RequestSizeLimitMiddleware."""

    def test_request_size_limit_allows_small_requests(self) -> None:
        """Test that small requests are allowed."""
        app = FastAPI()
        app.add_middleware(
            RequestSizeLimitMiddleware,
            max_size_bytes=1000,
        )

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
        app.add_middleware(
            RequestSizeLimitMiddleware,
            max_size_bytes=100,
        )

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

    def test_request_size_limit_includes_error_message(self) -> None:
        """Test that 413 response includes helpful error message."""
        app = FastAPI()
        app.add_middleware(
            RequestSizeLimitMiddleware,
            max_size_bytes=100,
        )

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
        data = response.json()
        assert "100 bytes" in data["detail"]


class TestCORSConfiguration:
    """Test CORS configuration."""

    def test_cors_config_development(self) -> None:
        """Test CORS config for development environment."""
        config = get_cors_config("development")

        assert "http://localhost:3000" in config["allow_origins"]
        assert "http://localhost:5173" in config["allow_origins"]
        assert config["allow_credentials"] is True
        assert "Content-Type" in config["allow_headers"]

    def test_cors_config_staging(self) -> None:
        """Test CORS config for staging environment."""
        config = get_cors_config("staging")

        assert "https://app-staging.lockdin.ai" in config["allow_origins"]
        assert config["allow_credentials"] is True

    def test_cors_config_production(self) -> None:
        """Test CORS config for production environment."""
        config = get_cors_config("production")

        assert "https://app.lockdin.ai" in config["allow_origins"]
        assert config["allow_credentials"] is True
        assert "http://" not in str(config["allow_origins"])

    def test_cors_config_includes_custom_headers(self) -> None:
        """Test that CORS config includes custom headers."""
        config = get_cors_config()

        assert "X-Correlation-ID" in config["allow_headers"]
        assert "X-Lockdin-Session-Token" in config["allow_headers"]


class TestCORSIntegration:
    """Test CORS middleware integration."""

    def test_cors_middleware_preflight_request(self) -> None:
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

    def test_cors_middleware_includes_credentials_header(self) -> None:
        """Test that CORS response includes credentials header."""
        app = FastAPI()
        cors_config = get_cors_config("development")
        app.add_middleware(CORSMiddleware, **cors_config)

        @app.get("/test")
        def test_endpoint() -> dict:
            return {"status": "ok"}

        client = TestClient(app)

        response = client.get(
            "/test",
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.status_code == 200
        assert "Access-Control-Allow-Credentials" in response.headers
