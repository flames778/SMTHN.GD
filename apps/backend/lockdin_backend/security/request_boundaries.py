"""Request boundary protections: rate limiting and request size validation for backend."""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimiter:
    """In-memory rate limiter using sliding window algorithm."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60) -> None:
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed per window.
            window_seconds: Time window in seconds.
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for the given key.

        Args:
            key: Identifier (e.g., user ID).

        Returns:
            True if request is allowed, False if rate limited.
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Remove old requests outside the window
        self.requests[key] = [
            req_time for req_time in self.requests[key] if req_time > window_start
        ]

        # Check if limit exceeded
        if len(self.requests[key]) >= self.max_requests:
            return False

        # Add current request
        self.requests[key].append(now)
        return True

    def get_reset_time(self, key: str) -> datetime:
        """Get when the rate limit resets for a key.

        Args:
            key: Identifier.

        Returns:
            Datetime when rate limit resets.
        """
        if not self.requests.get(key):
            return datetime.now(timezone.utc)

        oldest_request = self.requests[key][0]
        reset_time = oldest_request + self.window_seconds
        return datetime.fromtimestamp(reset_time, tz=timezone.utc)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests by user ID."""

    def __init__(self, app, max_requests: int = 500, window_seconds: int = 60) -> None:
        """Initialize rate limit middleware.

        Args:
            app: FastAPI app instance.
            max_requests: Max requests per window per user.
            window_seconds: Time window in seconds.
        """
        super().__init__(app)
        self.limiter = RateLimiter(max_requests, window_seconds)

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Rate limit incoming requests by user.

        Args:
            request: Incoming request.
            call_next: Next middleware/endpoint.

        Returns:
            Response (429 if rate limited).
        """
        # Use user ID from token or IP as fallback
        user_id = request.headers.get("x-user-id", request.client.host if request.client else "unknown")

        if not self.limiter.is_allowed(user_id):
            reset_time = self.limiter.get_reset_time(user_id)
            return JSONResponse(
                status_code=429,
                content={
                    "type": "https://api.lockdin.ai/errors/rate-limit-exceeded",
                    "status": 429,
                    "title": "Too Many Requests",
                    "detail": f"Rate limit exceeded. Reset at {reset_time.isoformat()}",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                },
                headers={"Retry-After": str(int(reset_time.timestamp()))},
            )

        return await call_next(request)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for enforcing maximum request body size."""

    def __init__(self, app, max_size_bytes: int = 10 * 1024 * 1024) -> None:
        """Initialize request size limit middleware.

        Args:
            app: FastAPI app instance.
            max_size_bytes: Maximum request body size in bytes (default: 10 MB).
        """
        super().__init__(app)
        self.max_size_bytes = max_size_bytes

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Check request size before processing.

        Args:
            request: Incoming request.
            call_next: Next middleware/endpoint.

        Returns:
            Response (413 if request too large).
        """
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "type": "https://api.lockdin.ai/errors/request-too-large",
                    "status": 413,
                    "title": "Payload Too Large",
                    "detail": f"Request exceeds maximum size of {self.max_size_bytes} bytes",
                    "error_code": "REQUEST_TOO_LARGE",
                },
            )

        return await call_next(request)
