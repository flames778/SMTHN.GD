"""API package."""

from app.api.consent import router as consent_router
from app.api.integrations import router as integrations_router

__all__ = ["consent_router", "integrations_router"]
