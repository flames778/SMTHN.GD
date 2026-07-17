"""Factory functions for creating test data.

Provides builders for common test entities like users, integrations, consent records, etc.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from lockdin_backend.persistence.identity import IdentityRepository


class UserFactory:
    """Factory for creating test users and sessions."""

    @staticmethod
    def create_owner(
        db: Session,
        display_name: str = "Test Owner",
        device_name: str = "Test Device",
        platform: str = "test",
    ) -> dict[str, Any]:
        """Create a bootstrapped owner user.

        Args:
            db: Database session.
            display_name: User display name.
            device_name: Device name.
            platform: Device platform.

        Returns:
            Dict with user_id, device_id, session_id, and token.
        """
        issued = IdentityRepository(db).bootstrap_first_user(
            display_name=display_name,
            device_name=device_name,
            platform=platform,
        )

        return {
            "user_id": issued.user_id,
            "device_id": issued.device_id,
            "session_id": issued.session_id,
            "token": issued.token,
            "display_name": display_name,
            "device_name": device_name,
            "platform": platform,
        }


class IntegrationFactory:
    """Factory for creating test integrations.

    Note: Actual integration creation requires app-layer
    (db models, repositories). This is a placeholder for future expansion.
    """

    @staticmethod
    def create_google_integration(
        user_id: str,
        provider: str = "google",
        access_token: str = "test-access-token",
        refresh_token: str = "test-refresh-token",
        expires_at: datetime | None = None,
    ) -> dict[str, Any]:
        """Create a test Google integration data dict.

        Args:
            user_id: User ID.
            provider: Provider name (default: google).
            access_token: OAuth access token.
            refresh_token: OAuth refresh token.
            expires_at: Token expiry time.

        Returns:
            Dict with integration data.
        """
        if expires_at is None:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        return {
            "user_id": user_id,
            "provider": provider,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
        }


class ConsentFactory:
    """Factory for creating test consent records."""

    @staticmethod
    def create_google_calendar_consent(
        user_id: str,
        dataset: str = "google_calendar",
        granularity: str = "event",
    ) -> dict[str, Any]:
        """Create a test consent record for Google Calendar.

        Args:
            user_id: User ID.
            dataset: Dataset name (default: google_calendar).
            granularity: Granularity level (default: event).

        Returns:
            Dict with consent data.
        """
        return {
            "user_id": user_id,
            "dataset": dataset,
            "granularity": granularity,
            "created_at": datetime.now(timezone.utc),
        }


class RequestFactory:
    """Factory for creating test request data."""

    @staticmethod
    def auth_headers(token: str) -> dict[str, str]:
        """Create authorization headers.

        Args:
            token: Session token.

        Returns:
            Dict with X-Lockdin-Session-Token header.
        """
        return {"X-Lockdin-Session-Token": token}

    @staticmethod
    def correlation_id_header(correlation_id: str) -> dict[str, str]:
        """Create correlation ID header.

        Args:
            correlation_id: Correlation ID.

        Returns:
            Dict with X-Correlation-ID header.
        """
        return {"X-Correlation-ID": correlation_id}

    @staticmethod
    def combined_headers(token: str, correlation_id: str) -> dict[str, str]:
        """Create combined auth and correlation ID headers.

        Args:
            token: Session token.
            correlation_id: Correlation ID.

        Returns:
            Dict with both headers.
        """
        return {
            "X-Lockdin-Session-Token": token,
            "X-Correlation-ID": correlation_id,
        }
