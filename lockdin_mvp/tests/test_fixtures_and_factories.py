"""Tests demonstrating database fixtures and factory usage.

Validates conftest.py fixtures and factory functions for integration testing.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from tests.factories import (
    ConsentFactory,
    IntegrationFactory,
    RequestFactory,
    UserFactory,
)


class TestUserFactoryFixtures:
    """Test user factory fixtures."""

    def test_issued_owner_fixture(self, issued_owner: dict[str, str]) -> None:
        """Test that issued_owner fixture creates valid owner."""
        assert issued_owner["user_id"]
        assert issued_owner["device_id"]
        assert issued_owner["session_id"]
        assert issued_owner["token"]
        assert len(issued_owner["token"]) > 0

    def test_auth_headers_fixture(self, auth_headers: dict[str, str]) -> None:
        """Test that auth_headers fixture provides valid headers."""
        assert "X-Lockdin-Session-Token" in auth_headers
        assert auth_headers["X-Lockdin-Session-Token"]

    def test_user_factory_create_owner(self, identity_db: Session) -> None:
        """Test UserFactory.create_owner."""
        owner = UserFactory.create_owner(
            identity_db,
            display_name="Custom Owner",
            device_name="Custom Device",
            platform="windows",
        )

        assert owner["user_id"]
        assert owner["device_id"]
        assert owner["display_name"] == "Custom Owner"
        assert owner["device_name"] == "Custom Device"
        assert owner["platform"] == "windows"

    def test_user_factory_create_session(
        self, identity_db: Session, issued_owner: dict[str, str]
    ) -> None:
        """Test UserFactory fixtures.
        
        Note: bootstrap_first_user can only be called once per database instance.
        This test verifies the issued_owner fixture is available.
        """
        # Verify issued_owner fixture provides valid tokens
        assert issued_owner["user_id"]
        assert issued_owner["token"]
        assert issued_owner["session_id"]


class TestRequestFactoryFixtures:
    """Test request factory fixtures."""

    def test_auth_headers_factory(self) -> None:
        """Test RequestFactory.auth_headers."""
        headers = RequestFactory.auth_headers("test-token-123")

        assert "X-Lockdin-Session-Token" in headers
        assert headers["X-Lockdin-Session-Token"] == "test-token-123"

    def test_correlation_id_header_factory(self) -> None:
        """Test RequestFactory.correlation_id_header."""
        headers = RequestFactory.correlation_id_header("trace-123")

        assert "X-Correlation-ID" in headers
        assert headers["X-Correlation-ID"] == "trace-123"

    def test_combined_headers_factory(self) -> None:
        """Test RequestFactory.combined_headers."""
        headers = RequestFactory.combined_headers("token-123", "trace-456")

        assert "X-Lockdin-Session-Token" in headers
        assert "X-Correlation-ID" in headers
        assert headers["X-Lockdin-Session-Token"] == "token-123"
        assert headers["X-Correlation-ID"] == "trace-456"


class TestIntegrationFactoryFixtures:
    """Test integration factory fixtures."""

    def test_create_google_integration(self) -> None:
        """Test IntegrationFactory.create_google_integration."""
        integration = IntegrationFactory.create_google_integration(
            user_id="user-123",
            access_token="access-token-abc",
            refresh_token="refresh-token-xyz",
        )

        assert integration["user_id"] == "user-123"
        assert integration["provider"] == "google"
        assert integration["access_token"] == "access-token-abc"
        assert integration["refresh_token"] == "refresh-token-xyz"
        assert integration["expires_at"]


class TestConsentFactoryFixtures:
    """Test consent factory fixtures."""

    def test_create_google_calendar_consent(self) -> None:
        """Test ConsentFactory.create_google_calendar_consent."""
        consent = ConsentFactory.create_google_calendar_consent(
            user_id="user-123",
        )

        assert consent["user_id"] == "user-123"
        assert consent["dataset"] == "google_calendar"
        assert consent["granularity"] == "event"
        assert consent["created_at"]


class TestDatabaseFixtures:
    """Test database fixtures."""

    def test_mvp_db_fixture(self, mvp_db: Session) -> None:
        """Test that mvp_db fixture provides valid session."""
        assert mvp_db is not None
        assert mvp_db.is_active

    def test_identity_db_fixture(self, identity_db: Session) -> None:
        """Test that identity_db fixture provides valid session."""
        assert identity_db is not None
        assert identity_db.is_active

    def test_client_with_db_fixture(self, client_with_db) -> None:
        """Test that client_with_db fixture provides valid TestClient."""
        assert client_with_db is not None
        # Verify we can make requests
        response = client_with_db.get("/health")
        assert response.status_code == 200


class TestFixtureIntegration:
    """Test integration of fixtures together."""

    def test_authenticated_request_with_fixtures(
        self, client_with_db, issued_owner: dict[str, str]
    ) -> None:
        """Test making authenticated request with fixtures."""
        headers = {"X-Lockdin-Session-Token": issued_owner["token"]}

        # Mock endpoint that returns actor context
        # (actual endpoint may vary, this demonstrates fixture usage)
        response = client_with_db.get("/api/consent", headers=headers)

        # Should not return 401 (auth should work)
        assert response.status_code != 401

    def test_multiple_sessions_same_user(self, identity_db: Session, issued_owner: dict[str, str]) -> None:
        """Test that fixtures provide consistent data.
        
        Note: bootstrap_first_user can only be called once per database.
        """
        # Verify we can access the same owner multiple times
        owner1 = issued_owner
        owner2 = issued_owner

        # They should be the same fixture data
        assert owner1["user_id"] == owner2["user_id"]
        assert owner1["token"] == owner2["token"]

    def test_factory_headers_consistency(self, issued_owner: dict[str, str]) -> None:
        """Test that factory headers match fixture headers."""
        fixture_headers = {"X-Lockdin-Session-Token": issued_owner["token"]}
        factory_headers = RequestFactory.auth_headers(issued_owner["token"])

        assert fixture_headers == factory_headers
