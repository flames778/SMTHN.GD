"""Structured correlation logging for request tracing.

Provides FastAPI middleware for correlation ID generation/extraction,
contextvars for request-scoped correlation data, and structured logging helpers.
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import uuid
from datetime import datetime
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Context variables for request-scoped data
_correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)
_user_id: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="")
_device_id: contextvars.ContextVar[str] = contextvars.ContextVar("device_id", default="")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to generate or extract correlation IDs for request tracing.
    
    - Checks for X-Correlation-ID header (external trace ID).
    - Generates UUID4 if not present.
    - Makes correlation_id available via get_correlation_id().
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Extract or generate correlation ID and set context var."""
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        _correlation_id.set(correlation_id)

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id

        return response


def get_correlation_id() -> str:
    """Retrieve the current request correlation ID from context."""
    return _correlation_id.get()


def set_actor_context(user_id: str = "", device_id: str = "") -> None:
    """Set actor identity in request context (for structured logging)."""
    if user_id:
        _user_id.set(user_id)
    if device_id:
        _device_id.set(device_id)


def get_actor_context() -> dict[str, str]:
    """Retrieve actor identity from request context."""
    return {
        "user_id": _user_id.get(),
        "device_id": _device_id.get(),
    }


class StructuredLogger:
    """Structured JSON logger with correlation context.
    
    Emits JSON-formatted logs with automatic correlation_id, timestamp,
    and structured fields for centralized log aggregation.
    """

    def __init__(self, name: str, level: int = logging.INFO) -> None:
        """Initialize logger.
        
        Args:
            name: Logger name (typically __name__).
            level: Logging level (default: INFO).
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Add JSON formatter if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                logging.Formatter('%(message)s')
            )
            self.logger.addHandler(handler)

    def _format_log(
        self,
        level: str,
        message: str,
        **kwargs: Any,
    ) -> str:
        """Format log entry as JSON with correlation context.
        
        Args:
            level: Log level (INFO, ERROR, etc.).
            message: Log message.
            **kwargs: Additional structured fields.
        
        Returns:
            JSON-formatted log string.
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": message,
            "correlation_id": get_correlation_id(),
            **get_actor_context(),
            **kwargs,
        }
        return json.dumps(log_entry)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log at INFO level."""
        self.logger.info(self._format_log("INFO", message, **kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        """Log at ERROR level."""
        self.logger.error(self._format_log("ERROR", message, **kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log at WARNING level."""
        self.logger.warning(self._format_log("WARNING", message, **kwargs))

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log at DEBUG level."""
        self.logger.debug(self._format_log("DEBUG", message, **kwargs))


# Convenience instance
logger = StructuredLogger(__name__)
