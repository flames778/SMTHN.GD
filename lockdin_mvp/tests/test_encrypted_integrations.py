"""Tests for encrypted integration token storage."""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import IntegrationTokenModel
from app.repositories.integrations import IntegrationRepository
from app.security.token_encryption import TokenEncryption


@pytest.fixture
def db_engine():
    """Create in-memory SQLite database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create database session."""
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def monkeypatch_encryption_key(monkeypatch):
    """Patch APP_ENCRYPTION_KEY in settings."""
    monkeypatch.setenv("APP_ENCRYPTION_KEY", "a" * 32)


class TestIntegrationRepositoryEncryption:
    """Test that integration repository encrypts tokens at rest."""

    def test_upsert_google_encrypts_tokens(self, db_session, monkeypatch_encryption_key):
        """Test that upsert_google encrypts access and refresh tokens."""
        repo = IntegrationRepository(db_session)

        user_id = "user123"
        access_token = "access_token_abc123"
        refresh_token = "refresh_token_xyz789"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        result = repo.upsert_google(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            scope="calendar gmail",
            token_type="Bearer",
            expires_at=expires_at,
        )

        assert result.user_id == user_id
        assert result.provider == "google"
        assert result.status == "connected"

        assert result.access_token != access_token
        assert result.refresh_token != refresh_token

        decrypted_tokens = repo.get_decrypted_tokens(result)
        assert decrypted_tokens["access_token"] == access_token
        assert decrypted_tokens["refresh_token"] == refresh_token

    def test_update_tokens_encrypts_new_tokens(self, db_session, monkeypatch_encryption_key):
        """Test that update_tokens encrypts new tokens."""
        repo = IntegrationRepository(db_session)

        user_id = "user123"
        first_token = repo.upsert_google(
            user_id=user_id,
            access_token="old_access_token",
            refresh_token="old_refresh_token",
            scope="calendar",
            token_type="Bearer",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        new_access = "new_access_token"
        new_refresh = "new_refresh_token"
        new_expires = datetime.now(timezone.utc) + timedelta(hours=2)

        updated = repo.update_tokens(
            row=first_token,
            access_token=new_access,
            refresh_token=new_refresh,
            expires_at=new_expires,
        )

        assert updated.access_token != new_access
        assert updated.refresh_token != new_refresh

        decrypted = repo.get_decrypted_tokens(updated)
        assert decrypted["access_token"] == new_access
        assert decrypted["refresh_token"] == new_refresh

    def test_revoke_encrypts_empty_tokens(self, db_session, monkeypatch_encryption_key):
        """Test that revoke encrypts empty strings for tokens."""
        repo = IntegrationRepository(db_session)

        row = repo.upsert_google(
            user_id="user123",
            access_token="token",
            refresh_token="refresh",
            scope="",
            token_type="Bearer",
            expires_at=None,
        )

        revoked = repo.revoke(row)
        assert revoked.status == "revoked"

        decrypted = repo.get_decrypted_tokens(revoked)
        assert decrypted["access_token"] == ""
        assert decrypted["refresh_token"] == ""

    def test_get_by_provider_returns_encrypted_tokens(self, db_session, monkeypatch_encryption_key):
        """Test that get_by_provider returns row with encrypted tokens."""
        repo = IntegrationRepository(db_session)

        user_id = "user456"
        access_token = "secret_access_token"
        refresh_token = "secret_refresh_token"

        repo.upsert_google(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            scope="",
            token_type="Bearer",
            expires_at=None,
        )

        retrieved = repo.get_by_provider(user_id=user_id, provider="google")
        assert retrieved is not None
        assert retrieved.access_token != access_token
        assert retrieved.refresh_token != refresh_token

        decrypted = repo.get_decrypted_tokens(retrieved)
        assert decrypted["access_token"] == access_token
        assert decrypted["refresh_token"] == refresh_token

    def test_list_for_user_returns_encrypted_tokens(self, db_session, monkeypatch_encryption_key):
        """Test that list_for_user returns rows with encrypted tokens."""
        repo = IntegrationRepository(db_session)

        user_id = "user789"
        access_token = "plaintext_access"
        refresh_token = "plaintext_refresh"

        repo.upsert_google(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            scope="",
            token_type="Bearer",
            expires_at=None,
        )

        rows = repo.list_for_user(user_id=user_id)
        assert len(rows) == 1

        row = rows[0]
        assert row.access_token != access_token
        assert row.refresh_token != refresh_token

        decrypted = repo.get_decrypted_tokens(row)
        assert decrypted["access_token"] == access_token
        assert decrypted["refresh_token"] == refresh_token

    def test_get_decrypted_tokens_invalid_ciphertext_returns_none(self, db_session, monkeypatch_encryption_key):
        """Test that get_decrypted_tokens handles invalid ciphertext gracefully."""
        repo = IntegrationRepository(db_session)

        row = repo.upsert_google(
            user_id="user",
            access_token="token",
            refresh_token="refresh",
            scope="",
            token_type="Bearer",
            expires_at=None,
        )

        row.access_token = "invalid_ciphertext"
        row.refresh_token = "also_invalid"

        decrypted = repo.get_decrypted_tokens(row)
        assert decrypted["access_token"] is None
        assert decrypted["refresh_token"] is None
