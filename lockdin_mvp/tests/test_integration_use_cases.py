"""Unit tests for integration use cases.

Tests the use-case layer in isolation using mocks — no HTTP, no database.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.application.integrations import (
    ConnectGoogleCommand,
    ConnectGoogleIntegration,
    IntegrationNotFoundError,
    ListIntegrations,
    OAuthCallback,
    OAuthCallbackCommand,
    OAuthCodeExchangeFailedError,
    OAuthStateInvalidError,
    OAuthTokenRefreshFailedError,
    RefreshIntegration,
    RefreshIntegrationCommand,
    RefreshTokenUnavailableError,
    RevokeIntegration,
    RevokeIntegrationCommand,
    UnsupportedIntegrationError,
)
from lockdin_backend.identity import ActorContext


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _actor(user_id: str = "user-1") -> ActorContext:
    return ActorContext(user_id=user_id, device_id="device-1", session_id="session-1")


def _make_row(
    provider: str = "google",
    status: str = "connected",
    user_id: str = "user-1",
) -> MagicMock:
    row = MagicMock()
    row.id = "int-1"
    row.user_id = user_id
    row.provider = provider
    row.scope = "calendar email"
    row.token_type = "Bearer"
    row.status = status
    row.expires_at = datetime(2030, 1, 1, tzinfo=timezone.utc)
    row.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    row.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return row


def _token_response() -> dict:
    return {
        "access_token": "access-abc",
        "refresh_token": "refresh-xyz",
        "scope": "calendar email",
        "token_type": "Bearer",
        "expires_at": datetime(2030, 1, 1, tzinfo=timezone.utc),
    }


# --------------------------------------------------------------------------- #
# ConnectGoogleIntegration
# --------------------------------------------------------------------------- #

class TestConnectGoogleIntegration:
    """Test ConnectGoogleIntegration use case."""

    def test_connect_exchanges_code_and_persists(self) -> None:
        """Test that connect exchanges the OAuth code and calls upsert_google."""
        repo = MagicMock()
        oauth = MagicMock()
        uow = MagicMock()

        repo.upsert_google.return_value = _make_row()
        oauth.exchange_code.return_value = _token_response()

        use_case = ConnectGoogleIntegration(repository=repo, oauth=oauth, unit_of_work=uow)
        result = use_case.execute(
            _actor(),
            ConnectGoogleCommand(auth_code="code-123", redirect_uri=None, scope=None),
        )

        oauth.exchange_code.assert_called_once_with("code-123", None)
        repo.upsert_google.assert_called_once()
        uow.commit.assert_called_once()
        assert result.provider == "google"
        assert result.status == "connected"

    def test_connect_raises_on_invalid_code(self) -> None:
        """Test that OAuthCodeExchangeFailedError is raised when exchange fails."""
        repo = MagicMock()
        oauth = MagicMock()
        uow = MagicMock()

        oauth.exchange_code.side_effect = ValueError("invalid code")

        use_case = ConnectGoogleIntegration(repository=repo, oauth=oauth, unit_of_work=uow)
        with pytest.raises(OAuthCodeExchangeFailedError):
            use_case.execute(
                _actor(),
                ConnectGoogleCommand(auth_code="bad", redirect_uri=None, scope=None),
            )

        uow.commit.assert_not_called()

    def test_connect_does_not_commit_on_error(self) -> None:
        """Test that commit is NOT called if an error occurs."""
        repo = MagicMock()
        oauth = MagicMock()
        uow = MagicMock()

        oauth.exchange_code.side_effect = ValueError("bad code")

        use_case = ConnectGoogleIntegration(repository=repo, oauth=oauth, unit_of_work=uow)
        with pytest.raises(OAuthCodeExchangeFailedError):
            use_case.execute(_actor(), ConnectGoogleCommand("bad", None, None))

        uow.commit.assert_not_called()


# --------------------------------------------------------------------------- #
# OAuthCallback
# --------------------------------------------------------------------------- #

class TestOAuthCallback:
    """Test OAuthCallback use case."""

    def test_callback_verifies_state_before_exchange(self) -> None:
        """Test that state is verified before exchanging the code."""
        repo = MagicMock()
        oauth = MagicMock()
        uow = MagicMock()

        oauth.verify_state.return_value = False

        use_case = OAuthCallback(repository=repo, oauth=oauth, unit_of_work=uow)
        with pytest.raises(OAuthStateInvalidError):
            use_case.execute(
                _actor(),
                OAuthCallbackCommand(code="c", state="bad-state", redirect_uri=None),
            )

        oauth.exchange_code.assert_not_called()
        uow.commit.assert_not_called()

    def test_callback_succeeds_with_valid_state(self) -> None:
        """Test that callback completes with valid state and code."""
        repo = MagicMock()
        oauth = MagicMock()
        uow = MagicMock()

        oauth.verify_state.return_value = True
        oauth.exchange_code.return_value = _token_response()
        repo.upsert_google.return_value = _make_row()

        use_case = OAuthCallback(repository=repo, oauth=oauth, unit_of_work=uow)
        result = use_case.execute(
            _actor(),
            OAuthCallbackCommand(code="valid-code", state="valid-state", redirect_uri=None),
        )

        uow.commit.assert_called_once()
        assert result.status == "connected"


# --------------------------------------------------------------------------- #
# RefreshIntegration
# --------------------------------------------------------------------------- #

class TestRefreshIntegration:
    """Test RefreshIntegration use case."""

    def test_refresh_raises_if_integration_not_found(self) -> None:
        """Test that IntegrationNotFoundError is raised if provider not found."""
        repo = MagicMock()
        oauth = MagicMock()
        uow = MagicMock()
        repo.get_by_provider.return_value = None

        use_case = RefreshIntegration(repository=repo, oauth=oauth, unit_of_work=uow)
        with pytest.raises(IntegrationNotFoundError):
            use_case.execute(_actor(), RefreshIntegrationCommand(provider="google"))

        uow.commit.assert_not_called()

    def test_refresh_raises_for_unsupported_provider(self) -> None:
        """Test that UnsupportedIntegrationError is raised for non-google."""
        repo = MagicMock()
        oauth = MagicMock()
        uow = MagicMock()
        repo.get_by_provider.return_value = _make_row(provider="notion")

        use_case = RefreshIntegration(repository=repo, oauth=oauth, unit_of_work=uow)
        with pytest.raises(UnsupportedIntegrationError):
            use_case.execute(_actor(), RefreshIntegrationCommand(provider="notion"))

        uow.commit.assert_not_called()

    def test_refresh_raises_when_no_refresh_token(self) -> None:
        """Test RefreshTokenUnavailableError when refresh token is missing."""
        repo = MagicMock()
        oauth = MagicMock()
        uow = MagicMock()
        repo.get_by_provider.return_value = _make_row()
        repo.get_decrypted_tokens.return_value = {"refresh_token": None, "access_token": "x"}

        use_case = RefreshIntegration(repository=repo, oauth=oauth, unit_of_work=uow)
        with pytest.raises(RefreshTokenUnavailableError):
            use_case.execute(_actor(), RefreshIntegrationCommand(provider="google"))

    def test_refresh_commits_on_success(self) -> None:
        """Test that refresh commits on successful token refresh."""
        repo = MagicMock()
        oauth = MagicMock()
        uow = MagicMock()

        row = _make_row()
        repo.get_by_provider.return_value = row
        repo.get_decrypted_tokens.return_value = {
            "refresh_token": "refresh-token",
            "access_token": "old-access",
        }
        oauth.refresh_token.return_value = _token_response()
        repo.update_tokens.return_value = row

        use_case = RefreshIntegration(repository=repo, oauth=oauth, unit_of_work=uow)
        result = use_case.execute(_actor(), RefreshIntegrationCommand(provider="google"))

        uow.commit.assert_called_once()
        assert result.status == "connected"

    def test_refresh_raises_on_oauth_failure(self) -> None:
        """Test OAuthTokenRefreshFailedError when token refresh call fails."""
        repo = MagicMock()
        oauth = MagicMock()
        uow = MagicMock()

        repo.get_by_provider.return_value = _make_row()
        repo.get_decrypted_tokens.return_value = {"refresh_token": "tok", "access_token": "x"}
        oauth.refresh_token.side_effect = ValueError("token expired")

        use_case = RefreshIntegration(repository=repo, oauth=oauth, unit_of_work=uow)
        with pytest.raises(OAuthTokenRefreshFailedError):
            use_case.execute(_actor(), RefreshIntegrationCommand(provider="google"))

        uow.commit.assert_not_called()


# --------------------------------------------------------------------------- #
# RevokeIntegration
# --------------------------------------------------------------------------- #

class TestRevokeIntegration:
    """Test RevokeIntegration use case."""

    def test_revoke_raises_if_not_found(self) -> None:
        """Test IntegrationNotFoundError when provider not found."""
        repo = MagicMock()
        uow = MagicMock()
        repo.get_by_provider.return_value = None

        use_case = RevokeIntegration(repository=repo, unit_of_work=uow)
        with pytest.raises(IntegrationNotFoundError):
            use_case.execute(_actor(), RevokeIntegrationCommand(provider="google"))

        uow.commit.assert_not_called()

    def test_revoke_commits_on_success(self) -> None:
        """Test that revoke commits on success."""
        repo = MagicMock()
        uow = MagicMock()

        row = _make_row(status="revoked")
        repo.get_by_provider.return_value = _make_row()
        repo.revoke.return_value = row

        use_case = RevokeIntegration(repository=repo, unit_of_work=uow)
        result = use_case.execute(_actor(), RevokeIntegrationCommand(provider="google"))

        uow.commit.assert_called_once()
        assert result.status == "revoked"


# --------------------------------------------------------------------------- #
# ListIntegrations
# --------------------------------------------------------------------------- #

class TestListIntegrations:
    """Test ListIntegrations use case."""

    def test_list_returns_empty_for_user_with_no_integrations(self) -> None:
        """Test list returns empty list when user has no integrations."""
        repo = MagicMock()
        repo.list_for_user.return_value = []

        use_case = ListIntegrations(repository=repo)
        results = use_case.execute(_actor())

        assert results == []

    def test_list_returns_all_integrations(self) -> None:
        """Test list returns all integrations for the user."""
        repo = MagicMock()
        repo.list_for_user.return_value = [_make_row(), _make_row(provider="notion")]

        use_case = ListIntegrations(repository=repo)
        results = use_case.execute(_actor())

        assert len(results) == 2
