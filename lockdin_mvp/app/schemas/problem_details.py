"""RFC 9457 Problem Details response models and utilities."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ProblemDetails(BaseModel):
    """RFC 9457 Problem Details response model.
    
    https://datatracker.ietf.org/doc/html/rfc9457
    
    Standard fields:
    - type: URI identifying problem type (e.g., "about:blank")
    - status: HTTP status code
    - title: Short human-readable summary
    - detail: Human-readable explanation specific to this occurrence
    - instance: URI identifying specific occurrence
    
    Additional fields for Lockdin:
    - error_code: Machine-readable error identifier
    - correlation_id: Request correlation ID for tracing
    """

    type: str = Field(
        default="about:blank",
        description="URI identifying the problem type",
        json_schema_extra={"example": "https://api.lockdin.ai/errors/invalid-oauth-state"},
    )
    status: int = Field(
        description="HTTP status code",
        json_schema_extra={"example": 400},
    )
    title: str = Field(
        description="Short, human-readable summary of the problem",
        json_schema_extra={"example": "Invalid OAuth State"},
    )
    detail: Optional[str] = Field(
        default=None,
        description="Human-readable explanation specific to this occurrence",
        json_schema_extra={"example": "OAuth state token expired or was tampered with"},
    )
    instance: Optional[str] = Field(
        default=None,
        description="URI identifying the specific occurrence",
        json_schema_extra={"example": "/api/integrations/google/callback?code=xyz"},
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Machine-readable error identifier",
        json_schema_extra={"example": "OAUTH_STATE_INVALID"},
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Request correlation ID for distributed tracing",
        json_schema_extra={"example": "req-2026-07-17T00:00:00.000Z-abc123"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "type": "https://api.lockdin.ai/errors/invalid-oauth-state",
                    "status": 400,
                    "title": "Invalid OAuth State",
                    "detail": "OAuth state token expired or was tampered with",
                    "instance": "/api/integrations/google/callback",
                    "error_code": "OAUTH_STATE_INVALID",
                    "correlation_id": "req-2026-07-17T00:00:00.000Z-abc123",
                }
            ]
        }
    }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict, excluding None values."""
        return self.model_dump(exclude_none=True)


# Standard error codes
ERROR_CODES = {
    # OAuth errors
    "OAUTH_STATE_INVALID": ("Invalid OAuth State", 400),
    "OAUTH_STATE_EXPIRED": ("OAuth State Expired", 400),
    "OAUTH_CODE_EXCHANGE_FAILED": ("OAuth Code Exchange Failed", 400),
    "OAUTH_TOKEN_REFRESH_FAILED": ("OAuth Token Refresh Failed", 400),
    # Integration errors
    "INTEGRATION_NOT_FOUND": ("Integration Not Found", 404),
    "INTEGRATION_NOT_CONNECTED": ("Integration Not Connected", 400),
    "UNSUPPORTED_INTEGRATION": ("Unsupported Integration", 400),
    "REFRESH_TOKEN_NOT_AVAILABLE": ("Refresh Token Not Available", 400),
    # Consent errors
    "CONSENT_RECORD_NOT_FOUND": ("Consent Record Not Found", 404),
    # Authentication errors
    "UNAUTHORIZED": ("Unauthorized", 401),
    "MISSING_SESSION_TOKEN": ("Missing Session Token", 401),
    "INVALID_SESSION_TOKEN": ("Invalid Session Token", 401),
    "SESSION_EXPIRED": ("Session Expired", 401),
    "SESSION_REVOKED": ("Session Revoked", 401),
    # Bootstrap errors
    "BOOTSTRAP_FAILED": ("Bootstrap Failed", 503),
    "INVALID_SETUP_SECRET": ("Invalid Setup Secret", 403),
    "OWNER_ALREADY_INITIALIZED": ("Owner Already Initialized", 409),
    # Internal errors
    "INTERNAL_SERVER_ERROR": ("Internal Server Error", 500),
    "SERVICE_UNAVAILABLE": ("Service Unavailable", 503),
}


def problem_details(
    error_code: str,
    status: int | None = None,
    detail: str | None = None,
    instance: str | None = None,
    correlation_id: str | None = None,
    **kwargs: Any,
) -> ProblemDetails:
    """Construct a ProblemDetails response.
    
    Args:
        error_code: Machine-readable error identifier
        status: HTTP status code (overrides default from ERROR_CODES)
        detail: Human-readable explanation
        instance: URI of the specific occurrence
        correlation_id: Request correlation ID
        **kwargs: Additional fields to include
    
    Returns:
        ProblemDetails instance
    """
    if error_code in ERROR_CODES:
        title, default_status = ERROR_CODES[error_code]
        if status is None:
            status = default_status
    else:
        title = "Unknown Error"
        if status is None:
            status = 500

    # Convert error_code to kebab-case for the type URL
    error_code_kebab = error_code.lower().replace("_", "-")

    return ProblemDetails(
        type=f"https://api.lockdin.ai/errors/{error_code_kebab}",
        status=status,
        title=title,
        detail=detail,
        instance=instance,
        error_code=error_code,
        correlation_id=correlation_id,
        **kwargs,
    )
