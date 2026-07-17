from __future__ import annotations

import os
import secrets
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from lockdin_backend.api.dependencies import IdentityDb
from lockdin_backend.persistence.identity import (
    BootstrapAlreadyCompletedError,
    IdentityRepository,
)

router = APIRouter(prefix="/api/session", tags=["session"])


class BootstrapSessionRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)
    device_name: str = Field(min_length=1, max_length=100)
    platform: str = Field(default="windows", min_length=1, max_length=32)


class BootstrapSessionResponse(BaseModel):
    user_id: str
    device_id: str
    session_id: str
    session_token: str
    expires_at: datetime


@router.post(
    "/bootstrap", response_model=BootstrapSessionResponse, status_code=status.HTTP_201_CREATED
)
def bootstrap_session(
    request: BootstrapSessionRequest,
    db: IdentityDb,
    bootstrap_token: Annotated[str | None, Header(alias="X-Lockdin-Bootstrap-Token")] = None,
) -> BootstrapSessionResponse:
    expected_token = os.getenv("APP_BOOTSTRAP_TOKEN")
    if not expected_token or len(expected_token) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session bootstrap is not configured",
        )
    if bootstrap_token is None or not secrets.compare_digest(bootstrap_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid bootstrap token",
        )

    try:
        issued = IdentityRepository(db).bootstrap_first_user(
            display_name=request.display_name,
            device_name=request.device_name,
            platform=request.platform,
        )
    except BootstrapAlreadyCompletedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return BootstrapSessionResponse(
        user_id=issued.user_id,
        device_id=issued.device_id,
        session_id=issued.session_id,
        session_token=issued.token,
        expires_at=issued.expires_at,
    )
