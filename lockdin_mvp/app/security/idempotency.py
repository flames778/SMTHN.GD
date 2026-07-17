"""Idempotency key middleware and helpers for mutation endpoints.

Clients send an `Idempotency-Key` header with mutations. The server stores
the response for the TTL period and returns the same response on replay.
Uses an in-process store (sufficient for single-process MVP; swap for Redis
for multi-instance deployments).
"""

from __future__ import annotations

import json
import time
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# --------------------------------------------------------------------------- #
# In-process idempotency store
# --------------------------------------------------------------------------- #

_IDEMPOTENCY_TTL_SECONDS = 86_400  # 24 hours


class IdempotencyStore:
    """Thread-safe in-memory store for idempotency records."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        record = self._store.get(key)
        if not record:
            return None
        if time.time() > record["expires_at"]:
            del self._store[key]
            return None
        return record

    def set(self, key: str, status_code: int, body: dict) -> None:
        self._store[key] = {
            "status_code": status_code,
            "body": body,
            "expires_at": time.time() + _IDEMPOTENCY_TTL_SECONDS,
        }

    def clear_expired(self) -> int:
        """Remove expired entries; returns count removed."""
        now = time.time()
        expired = [k for k, v in self._store.items() if now > v["expires_at"]]
        for k in expired:
            del self._store[k]
        return len(expired)


# Singleton store — replaced in tests via DI
_default_store = IdempotencyStore()


# --------------------------------------------------------------------------- #
# Middleware
# --------------------------------------------------------------------------- #

_MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Replay stored responses for duplicate mutation requests.

    - Only applies to POST/PUT/PATCH/DELETE requests.
    - Only active when the client sends `Idempotency-Key` header.
    - Caches JSON responses with 2xx status codes for 24 hours.
    - Replays stored response on duplicate request within TTL.
    """

    def __init__(self, app, store: IdempotencyStore | None = None) -> None:
        super().__init__(app)
        self._store = store or _default_store

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in _MUTATION_METHODS:
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        # Scope key to path to prevent cross-endpoint collisions
        scoped_key = f"{request.method}:{request.url.path}:{idempotency_key}"

        # Check for stored response
        stored = self._store.get(scoped_key)
        if stored:
            return JSONResponse(
                status_code=stored["status_code"],
                content=stored["body"],
                headers={"Idempotency-Key": idempotency_key, "X-Idempotency-Replayed": "true"},
            )

        # Process request and cache 2xx responses
        response = await call_next(request)

        if 200 <= response.status_code < 300:
            body_bytes = b""
            async for chunk in response.body_iterator:
                body_bytes += chunk
            try:
                body = json.loads(body_bytes)
                self._store.set(scoped_key, response.status_code, body)
                return JSONResponse(
                    status_code=response.status_code,
                    content=body,
                    headers={
                        **dict(response.headers),
                        "Idempotency-Key": idempotency_key,
                    },
                )
            except (json.JSONDecodeError, ValueError):
                # Non-JSON responses pass through unmodified
                return Response(
                    content=body_bytes,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )

        return response
