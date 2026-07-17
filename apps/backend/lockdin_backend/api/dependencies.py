from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from lockdin_backend.identity import ActorContext
from lockdin_backend.persistence.database import get_identity_db
from lockdin_backend.persistence.identity import IdentityRepository

IdentityDb = Annotated[Session, Depends(get_identity_db)]


def get_actor_context(
    db: IdentityDb,
    session_token: Annotated[str | None, Header(alias="X-Lockdin-Session-Token")] = None,
) -> ActorContext:
    actor = IdentityRepository(db).resolve_actor(session_token) if session_token else None
    if actor is not None:
        return actor

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "type": "https://lockdin.local/problems/actor-context-required",
            "title": "Authenticated session required",
            "status": status.HTTP_401_UNAUTHORIZED,
            "detail": "X-Lockdin-Session-Token is missing, invalid, expired, or revoked",
        },
    )


ActorDependency = Annotated[ActorContext, Depends(get_actor_context)]
