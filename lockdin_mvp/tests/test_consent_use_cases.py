"""Unit tests for consent use cases."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.application.consent import (
    ConsentNotFoundError,
    ConsentResult,
    DeleteConsent,
    DeleteConsentCommand,
    ListConsents,
    UpsertConsent,
    UpsertConsentCommand,
)
from lockdin_backend.identity import ActorContext


def _actor(user_id: str = "user-1") -> ActorContext:
    return ActorContext(user_id=user_id, device_id="device-1", session_id="session-1")


def _make_consent_row(user_id: str = "user-1", granted: bool = True) -> MagicMock:
    row = MagicMock()
    row.id = "consent-1"
    row.user_id = user_id
    row.integration = "google"
    row.data_category = "calendar"
    row.purpose = "scheduling"
    row.granted = granted
    row.granted_at = datetime(2025, 1, 1, tzinfo=timezone.utc) if granted else None
    row.revoked_at = None if granted else datetime(2025, 1, 1, tzinfo=timezone.utc)
    row.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    row.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return row


class TestUpsertConsent:
    """Test UpsertConsent use case."""

    def test_upsert_calls_repository_and_commits(self) -> None:
        """Test that upsert calls repository and commits on success."""
        repo = MagicMock()
        uow = MagicMock()
        repo.upsert.return_value = _make_consent_row()

        use_case = UpsertConsent(repository=repo, unit_of_work=uow)
        result = use_case.execute(
            _actor(),
            UpsertConsentCommand(
                integration="google",
                data_category="calendar",
                purpose="scheduling",
                granted=True,
            ),
        )

        repo.upsert.assert_called_once_with(
            user_id="user-1",
            integration="google",
            data_category="calendar",
            purpose="scheduling",
            granted=True,
        )
        uow.commit.assert_called_once()
        assert result.integration == "google"
        assert result.granted is True

    def test_upsert_returns_consent_result(self) -> None:
        """Test that upsert returns a ConsentResult dataclass."""
        repo = MagicMock()
        uow = MagicMock()
        repo.upsert.return_value = _make_consent_row()

        use_case = UpsertConsent(repository=repo, unit_of_work=uow)
        result = use_case.execute(
            _actor(),
            UpsertConsentCommand("google", "calendar", "scheduling", True),
        )

        assert isinstance(result, ConsentResult)


class TestListConsents:
    """Test ListConsents use case."""

    def test_list_returns_empty_for_no_consents(self) -> None:
        """Test list returns empty when user has no consents."""
        repo = MagicMock()
        repo.list_for_user.return_value = []

        use_case = ListConsents(repository=repo)
        results = use_case.execute(_actor())

        assert results == []
        repo.list_for_user.assert_called_once_with("user-1")

    def test_list_returns_all_consents(self) -> None:
        """Test list returns all consents for the user."""
        repo = MagicMock()
        repo.list_for_user.return_value = [_make_consent_row(), _make_consent_row(granted=False)]

        use_case = ListConsents(repository=repo)
        results = use_case.execute(_actor())

        assert len(results) == 2


class TestDeleteConsent:
    """Test DeleteConsent use case."""

    def test_delete_succeeds_and_commits(self) -> None:
        """Test delete commits on successful deletion."""
        repo = MagicMock()
        uow = MagicMock()
        repo.delete.return_value = True

        use_case = DeleteConsent(repository=repo, unit_of_work=uow)
        use_case.execute(_actor(), DeleteConsentCommand(consent_id="consent-1"))

        repo.delete.assert_called_once_with("user-1", "consent-1")
        uow.commit.assert_called_once()

    def test_delete_raises_if_not_found(self) -> None:
        """Test ConsentNotFoundError when consent doesn't exist."""
        repo = MagicMock()
        uow = MagicMock()
        repo.delete.return_value = False

        use_case = DeleteConsent(repository=repo, unit_of_work=uow)
        with pytest.raises(ConsentNotFoundError) as exc_info:
            use_case.execute(_actor(), DeleteConsentCommand(consent_id="missing"))

        assert "missing" in str(exc_info.value)
        uow.commit.assert_not_called()

    def test_delete_does_not_commit_on_not_found(self) -> None:
        """Test that commit is NOT called when deletion fails."""
        repo = MagicMock()
        uow = MagicMock()
        repo.delete.return_value = False

        use_case = DeleteConsent(repository=repo, unit_of_work=uow)
        with pytest.raises(ConsentNotFoundError):
            use_case.execute(_actor(), DeleteConsentCommand(consent_id="gone"))

        uow.commit.assert_not_called()
