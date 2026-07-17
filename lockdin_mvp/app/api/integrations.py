from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from lockdin_backend.api.dependencies import ActorDependency
from sqlalchemy.orm import Session

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
from app.services.oauth_google import GoogleOAuthService
from app.workers.tasks import sync_google_integrations

router = APIRouter(prefix="/api/integrations", tags=["integrations"])
DbSession = Annotated[Session, Depends(get_db)]
AuthorizeRequest = Annotated[IntegrationAuthorizeUrlRequest, Depends()]


@router.get("/google/authorize-url", response_model=IntegrationAuthorizeUrlResponse)
def google_authorize_url(request: AuthorizeRequest, actor: ActorDependency) -> IntegrationAuthorizeUrlResponse:
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
    oauth = GoogleOAuthService()
    if not oauth.verify_state(state=state, user_id=actor.user_id):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    try:
        token = oauth.exchange_code(code, redirect_uri)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    row = IntegrationRepository(db).upsert_google(
        user_id=actor.user_id,
        access_token=token["access_token"],
        refresh_token=token["refresh_token"],
        scope=token.get("scope", ""),
        token_type=token.get("token_type", "Bearer"),
        expires_at=token["expires_at"],
    )
    return IntegrationRead.model_validate(row)


@router.post("/google/connect", response_model=IntegrationRead)
def connect_google(
    request: IntegrationConnectRequest,
    actor: ActorDependency,
    db: DbSession,
) -> IntegrationRead:
    oauth = GoogleOAuthService()
    try:
        token = oauth.exchange_code(request.auth_code, request.redirect_uri)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    row = IntegrationRepository(db).upsert_google(
        user_id=actor.user_id,
        access_token=token["access_token"],
        refresh_token=token["refresh_token"],
        scope=token.get("scope") or request.scope,
        token_type=token["token_type"],
        expires_at=token["expires_at"],
    )
    return IntegrationRead.model_validate(row)


@router.post("/{provider}/refresh", response_model=IntegrationRead)
def refresh_integration(provider: str, actor: ActorDependency, db: DbSession) -> IntegrationRead:
    repo = IntegrationRepository(db)
    row = repo.get_by_provider(user_id=actor.user_id, provider=provider)
    if not row:
        raise HTTPException(status_code=404, detail=f"Integration {provider} not found")

    if provider != "google":
        raise HTTPException(status_code=400, detail="Only google refresh is supported in MVP")

    oauth = GoogleOAuthService()
    try:
        refreshed = oauth.refresh_token(row.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    updated = repo.update_tokens(
        row=row,
        access_token=refreshed["access_token"],
        refresh_token=refreshed["refresh_token"],
        expires_at=refreshed["expires_at"],
    )
    return IntegrationRead.model_validate(updated)


@router.post("/{provider}/revoke", response_model=IntegrationRead)
def revoke_integration(provider: str, actor: ActorDependency, db: DbSession) -> IntegrationRead:
    repo = IntegrationRepository(db)
    row = repo.get_by_provider(user_id=actor.user_id, provider=provider)
    if not row:
        raise HTTPException(status_code=404, detail=f"Integration {provider} not found")

    revoked = repo.revoke(row)
    return IntegrationRead.model_validate(revoked)


@router.get("", response_model=list[IntegrationRead])
def list_integrations(actor: ActorDependency, db: DbSession) -> list[IntegrationRead]:
    rows = IntegrationRepository(db).list_for_user(user_id=actor.user_id)
    return [IntegrationRead.model_validate(row) for row in rows]


@router.post("/google/sync", response_model=GoogleSyncResponse)
def sync_google(request: GoogleSyncRequest, actor: ActorDependency) -> GoogleSyncResponse:
    if request.run_inline:
        stats = sync_google_integrations(actor.user_id)
        return GoogleSyncResponse(status="completed", stats=stats)

    task = sync_google_integrations.delay(actor.user_id)
    return GoogleSyncResponse(status="queued", task_id=str(task.id))
