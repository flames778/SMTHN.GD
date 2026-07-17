"""FastAPI exception handlers for RFC 9457 Problem Details responses."""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from fastapi import FastAPI, HTTPException, status

from app.core.logging import get_correlation_id
from app.schemas.problem_details import ProblemDetails, problem_details


class ProblemDetailsException(Exception):
    """Custom exception that wraps a ProblemDetails response."""

    def __init__(self, details: ProblemDetails) -> None:
        self.details = details
        super().__init__(str(details))


async def problem_details_exception_handler(
    request: Request, exc: ProblemDetailsException
) -> JSONResponse:
    """Handle ProblemDetailsException and return RFC 9457 response."""
    # Inject correlation_id if not already set
    if not exc.details.correlation_id:
        exc.details.correlation_id = get_correlation_id()
    
    return JSONResponse(
        status_code=exc.details.status,
        content=exc.details.to_dict(),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Convert FastAPI HTTPException to RFC 9457 Problem Details.
    
    If detail already contains error_code and other problem fields, preserve them.
    Otherwise, infer from status code.
    """
    # Check if detail is already a ProblemDetails dict
    if isinstance(exc.detail, dict) and "error_code" in exc.detail:
        # Already formatted; inject correlation_id if missing
        if not exc.detail.get("correlation_id"):
            exc.detail["correlation_id"] = get_correlation_id()
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )

    # Map HTTP status codes to error codes and titles
    status_to_error_code = {
        status.HTTP_400_BAD_REQUEST: ("BAD_REQUEST", "Bad Request"),
        status.HTTP_401_UNAUTHORIZED: ("UNAUTHORIZED", "Unauthorized"),
        status.HTTP_403_FORBIDDEN: ("FORBIDDEN", "Forbidden"),
        status.HTTP_404_NOT_FOUND: ("NOT_FOUND", "Not Found"),
        status.HTTP_409_CONFLICT: ("CONFLICT", "Conflict"),
        status.HTTP_500_INTERNAL_SERVER_ERROR: ("INTERNAL_SERVER_ERROR", "Internal Server Error"),
        status.HTTP_503_SERVICE_UNAVAILABLE: ("SERVICE_UNAVAILABLE", "Service Unavailable"),
    }

    error_code, title = status_to_error_code.get(
        exc.status_code, ("UNKNOWN_ERROR", "Unknown Error")
    )

    details = ProblemDetails(
        type=f"https://api.lockdin.ai/errors/{error_code.lower().replace('_', '-')}",
        status=exc.status_code,
        title=title,
        detail=str(exc.detail) if exc.detail else None,
        error_code=error_code,
        correlation_id=get_correlation_id(),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=details.to_dict(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unexpected exceptions and return RFC 9457 Problem Details."""
    details = problem_details(
        error_code="INTERNAL_SERVER_ERROR",
        status=HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred. Please try again later.",
        correlation_id=get_correlation_id(),
    )

    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content=details.to_dict(),
    )


def register_problem_details_handlers(app: FastAPI) -> None:
    """Register all RFC 9457 problem details exception handlers with FastAPI."""
    app.add_exception_handler(ProblemDetailsException, problem_details_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
