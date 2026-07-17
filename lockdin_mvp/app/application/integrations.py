"""Integration use cases: connect, refresh, revoke, list Google OAuth integrations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from lockdin_backend.identity import ActorContext


# --------------------------------------------------------------------------- #
# Domain result types (decouple use cases from ORM models)
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class IntegrationResult:
    id: str
    user_id: str
    provider: str
    scope: str
    token_type: str
    status: str
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------- #
# Repository and UoW protocols
# --------------------------------------------------------------------------- #

class IntegrationRow(Protocol):
    """Minimal protocol for an integration ORM row."""
    id: str
    user_id: str
    provider: str
    scope: str
    token_type: str
    status: str
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


class IntegrationRepository(Protocol):
    def upsert_google(
        self,
        *,
        user_id: str,
        access_token: str,
        refresh_token: str,
        scope: str,
        token_type: str,
        expires_at: datetime | None,
    ) -> IntegrationRow: ...

    def get_by_provider(self, user_id: str, provider: str) -> IntegrationRow | None: ...

    def list_for_user(self, user_id: str) -> list[IntegrationRow]: ...

    def update_tokens(
        self,
        row: IntegrationRow,
        *,
        access_token: str,
        refresh_token: str,
        expires_at: datetime | None,
    ) -> IntegrationRow: ...

    def revoke(self, row: IntegrationRow) -> IntegrationRow: ...

    def get_decrypted_tokens(self, row: IntegrationRow) -> dict[str, str | None]: ...


class OAuthService(Protocol):
    def exchange_code(self, code: str, redirect_uri: str | None) -> dict: ...
    def refresh_token(self, refresh_token: str) -> dict: ...
    def build_authorize_url(self, *, user_id: str, redirect_uri: str | None, scope: str | None) -> dict: ...
    def verify_state(self, *, state: str, user_id: str) -> bool: ...


class UnitOfWork(Protocol):
    def commit(self) -> None: ...


# --------------------------------------------------------------------------- #
# Command / query objects
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class ConnectGoogleCommand:
    auth_code: str
    redirect_uri: str | None
    scope: str | None


@dataclass(frozen=True, slots=True)
class OAuthCallbackCommand:
    code: str
    state: str
    redirect_uri: str | None


@dataclass(frozen=True, slots=True)
class RefreshIntegrationCommand:
    provider: str


@dataclass(frozen=True, slots=True)
class RevokeIntegrationCommand:
    provider: str


# --------------------------------------------------------------------------- #
# Custom exceptions (raised by use cases, mapped to HTTP in the route layer)
# --------------------------------------------------------------------------- #

class IntegrationNotFoundError(Exception):
    def __init__(self, provider: str) -> None:
        super().__init__(f"Integration '{provider}' not found")
        self.provider = provider


class OAuthStateInvalidError(Exception):
    pass


class OAuthCodeExchangeFailedError(Exception):
    pass


class OAuthTokenRefreshFailedError(Exception):
    pass


class UnsupportedIntegrationError(Exception):
    def __init__(self, provider: str) -> None:
        super().__init__(f"Provider '{provider}' is not supported for this operation")
        self.provider = provider


class RefreshTokenUnavailableError(Exception):
    pass


# --------------------------------------------------------------------------- #
# Use cases
# --------------------------------------------------------------------------- #

def _row_to_result(row: IntegrationRow) -> IntegrationResult:
    return IntegrationResult(
        id=row.id,
        user_id=row.user_id,
        provider=row.provider,
        scope=row.scope,
        token_type=row.token_type,
        status=row.status,
        expires_at=row.expires_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class ConnectGoogleIntegration:
    """Exchange an OAuth code and persist the integration.

    Owns the transaction boundary: commits only on full success.
    """

    def __init__(
        self,
        repository: IntegrationRepository,
        oauth: OAuthService,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._oauth = oauth
        self._unit_of_work = unit_of_work

    def execute(self, actor: ActorContext, command: ConnectGoogleCommand) -> IntegrationResult:
        try:
            token = self._oauth.exchange_code(command.auth_code, command.redirect_uri)
        except ValueError as exc:
            raise OAuthCodeExchangeFailedError(str(exc)) from exc

        row = self._repository.upsert_google(
            user_id=actor.user_id,
            access_token=token["access_token"],
            refresh_token=token["refresh_token"],
            scope=token.get("scope") or command.scope or "",
            token_type=token.get("token_type", "Bearer"),
            expires_at=token.get("expires_at"),
        )
        self._unit_of_work.commit()
        return _row_to_result(row)


class OAuthCallback:
    """Handle an OAuth callback: verify state, exchange code, persist.

    Owns the transaction boundary.
    """

    def __init__(
        self,
        repository: IntegrationRepository,
        oauth: OAuthService,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._oauth = oauth
        self._unit_of_work = unit_of_work

    def execute(self, actor: ActorContext, command: OAuthCallbackCommand) -> IntegrationResult:
        if not self._oauth.verify_state(state=command.state, user_id=actor.user_id):
            raise OAuthStateInvalidError("OAuth state token expired or was tampered with")

        try:
            token = self._oauth.exchange_code(command.code, command.redirect_uri)
        except ValueError as exc:
            raise OAuthCodeExchangeFailedError(str(exc)) from exc

        row = self._repository.upsert_google(
            user_id=actor.user_id,
            access_token=token["access_token"],
            refresh_token=token["refresh_token"],
            scope=token.get("scope", ""),
            token_type=token.get("token_type", "Bearer"),
            expires_at=token.get("expires_at"),
        )
        self._unit_of_work.commit()
        return _row_to_result(row)


class RefreshIntegration:
    """Refresh an integration's OAuth tokens.

    Owns the transaction boundary.
    """

    def __init__(
        self,
        repository: IntegrationRepository,
        oauth: OAuthService,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._oauth = oauth
        self._unit_of_work = unit_of_work

    def execute(self, actor: ActorContext, command: RefreshIntegrationCommand) -> IntegrationResult:
        row = self._repository.get_by_provider(actor.user_id, command.provider)
        if not row:
            raise IntegrationNotFoundError(command.provider)

        if command.provider != "google":
            raise UnsupportedIntegrationError(command.provider)

        tokens = self._repository.get_decrypted_tokens(row)
        if not tokens.get("refresh_token"):
            raise RefreshTokenUnavailableError("Refresh token not available")

        try:
            refreshed = self._oauth.refresh_token(tokens["refresh_token"])
        except ValueError as exc:
            raise OAuthTokenRefreshFailedError(str(exc)) from exc

        updated = self._repository.update_tokens(
            row,
            access_token=refreshed["access_token"],
            refresh_token=refreshed["refresh_token"],
            expires_at=refreshed.get("expires_at"),
        )
        self._unit_of_work.commit()
        return _row_to_result(updated)


class RevokeIntegration:
    """Revoke an integration, clearing stored tokens.

    Owns the transaction boundary.
    """

    def __init__(
        self,
        repository: IntegrationRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    def execute(self, actor: ActorContext, command: RevokeIntegrationCommand) -> IntegrationResult:
        row = self._repository.get_by_provider(actor.user_id, command.provider)
        if not row:
            raise IntegrationNotFoundError(command.provider)

        revoked = self._repository.revoke(row)
        self._unit_of_work.commit()
        return _row_to_result(revoked)


class ListIntegrations:
    """List all integrations for the current actor."""

    def __init__(self, repository: IntegrationRepository) -> None:
        self._repository = repository

    def execute(self, actor: ActorContext) -> list[IntegrationResult]:
        rows = self._repository.list_for_user(actor.user_id)
        return [_row_to_result(row) for row in rows]
