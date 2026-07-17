"""RFC 9457 Problem Details response models and utilities."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ProblemDetails(BaseModel):
    """RFC 9457 Problem Details response model."""

    type: str = Field(
        default="about:blank",
        description="URI identifying the problem type",
    )
    status: int = Field(description="HTTP status code")
    title: str = Field(description="Short human-readable summary")
    detail: Optional[str] = Field(default=None, description="Problem-specific explanation")
    instance: Optional[str] = Field(default=None, description="URI of specific occurrence")
    error_code: Optional[str] = Field(default=None, description="Machine-readable error ID")
    correlation_id: Optional[str] = Field(default=None, description="Request correlation ID")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict, excluding None values."""
        return self.model_dump(exclude_none=True)
