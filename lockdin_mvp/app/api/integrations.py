"""Integration API routes - thin layer over application use cases."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from lockdin_backend.api.dependencies import ActorDependency
from sqlalchemy.orm import Session

from app.application.integrations import (
    ConnectGoogleCommand,
    ConnectGoogleIntegration,
    IntegrationNotFoundError,
    IntegrationResult,
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
from app.db.session import get_db
from app.repositories.integrations import IntegrationRepository
from app.schemas.integration import (
    GoogleSyncRequest,
    GoogleSyncResponse,
    IntegrationAuthorizeUrlRequest,
    IntegrationAuthorizeUrlResponse,
    IntegrationConnectRequest,
    IntegrationRead,
)
from app.schemas.problem_details import problem_details
from app.services.oauth_google import GoogleOAuthService
from app.workers.tasks import sync_google_integrations

router = APIRouter(prefix="/api/integrations", tags=["integrations"])
DbSession = Annotated[Session, Depends(get_db)]
AuthorizeRequest = Annotated[IntegrationAuthorizeUrlRequest, Depends()]


def _to_read(result: IntegrationResult) -> IntegrationRead:
    return IntegrationRead(
        id=result.id,
        user_id=result.user_id,
        provider=result.provider,
        scope=result.scope,
        token_type=result.token_type,
        status=result.status,
        expires_at=result.expires_at,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.get("/google/authorize-url", response_model=IntegrationAuthorizeUrlResponse)
def google_authorize_url(
    request: AuthorizeRequest, actor: ActorDependency
) -> IntegrationAuthorizeUrlResponse:
    oauth = GoogleOAuthService()
    result = oauth.build_authorize_url(
        user_id=actor.user_id,
        redirect_uri=request.redirect_uri,
        scope=request.scope,
    )
    return IntegrationAuthorizeUrlResponse(**result)


@router.get("/google/callback", response_model=IntegrationRead)
def google_callback(
    code: str,
    state: str,
    actor: ActorDependency,
    db: DbSession,
    redirect_uri: str | None = None,
) -> IntegrationRead:
    use_case = OAuthCallback(
        repository=IntegrationRepository(db),
        oauth=GoogleOAuthService(),
        unit_of_work=db,
    )
    try:
        result = use_case.execute(actor, OAuthCallbackCommand(code=code, state=state, redirect_uri=redirect_uri))
    except OAuthStateInvalidError as exc:
        raise HTTPException(
            status_code=400,
            detail=problem_details(error_code="OAUTH_STATE_INVALID", detail=str(exc)).to_dict(),
        ) from exc
    except OAuthCodeExchangeFailedError as exc:
        raise HTTPException(
            status_code=400,
            detail=problem_details(error_code="OAUTH_CODE_EXCHANGE_FAILED", detail=str(exc)).to_dict(),
        ) from exc
    return _to_read(result)


@router.post("/google/connect", response_model=IntegrationRead)
def connect_google(
    request: IntegrationConnectRequest,
    actor: ActorDependency,
    db: DbSession,
) -> IntegrationRead:
    use_case = ConnectGoogleIntegration(
        repository=IntegrationRepository(db),
        oauth=GoogleOAuthService(),
        unit_of_work=db,
    )
    try:
        result = use_case.execute(
            actor,
            ConnectGoogleCommand(
                auth_code=request.auth_code,
                redirect_uri=request.redirect_uri,
                scope=request.scope,
            ),
        )
    except OAuthCodeExchangeFailedError as exc:
        raise HTTPException(
            status_code=400,
            detail=problem_details(error_code="OAUTH_CODE_EXCHANGE_FAILED", detail=str(exc)).to_dict(),
        ) from exc
    return _to_read(result)


@router.post("/{provider}/refresh", response_model=IntegrationRead)
def refresh_integration(provider: str, actor: ActorDependency, db: DbSession) -> IntegrationRead:
    use_case = RefreshIntegration(
        repository=IntegrationRepository(db),
        oauth=GoogleOAuthService(),
        unit_of_work=db,
    )
    try:
        result = use_case.execute(actor, RefreshIntegrationCommand(provider=provider))
    except IntegrationNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=problem_details(error_code="INTEGRATION_NOT_FOUND", detail=str(exc)).to_dict(),
        ) from exc
    except UnsupportedIntegrationError as exc:
        raise HTTPException(
            status_code=400,
            detail=problem_details(error_code="UNSUPPORTED_INTEGRATION", detail=str(exc)).to_dict(),
        ) from exc
    except RefreshTokenUnavailableError as exc:
        raise HTTPException(
            status_code=400,
            detail=problem_details(error_code="REFRESH_TOKEN_NOT_AVAILABLE", detail=str(exc)).to_dict(),
        ) from exc
    except OAuthTokenRefreshFailedError as exc:
        raise HTTPException(
            status_code=400,
            detail=problem_details(error_code="OAUTH_TOKEN_REFRESH_FAILED", detail=str(exc)).to_dict(),
        ) from exc
    return _to_read(result)


@router.post("/{provider}/revoke", response_model=IntegrationRead)
def revoke_integration(provider: str, actor: ActorDependency, db: DbSession) -> IntegrationRead:
    use_case = RevokeIntegration(
        repository=IntegrationRepository(db),
        unit_of_work=db,
    )
    try:
        result = use_case.execute(actor, RevokeIntegrationCommand(provider=provider))
    except IntegrationNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=problem_details(error_code="INTEGRATION_NOT_FOUND", detail=str(exc)).to_dict(),
        ) from exc
    return _to_read(result)


@router.get("", response_model=list[IntegrationRead])
def list_integrations(actor: ActorDependency, db: DbSession) -> list[IntegrationRead]:
    use_case = ListIntegrations(repository=IntegrationRepository(db))
    return [_to_read(r) for r in use_case.execute(actor)]


@router.post("/google/sync", response_model=GoogleSyncResponse)
def sync_google(request: GoogleSyncRequest, actor: ActorDependency) -> GoogleSyncResponse:
    if request.run_inline:
        stats = sync_google_integrations(actor.user_id)
        return GoogleSyncResponse(status="completed", stats=stats)

    task = sync_google_integrations.delay(actor.user_id)
    return GoogleSyncResponse(status="queued", task_id=str(task.id))
