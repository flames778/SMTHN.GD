from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from lockdin_backend.domain.problem_details import ProblemDetails
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

    details = ProblemDetails(
        type="https://api.lockdin.ai/errors/unauthorized",
        status=status.HTTP_401_UNAUTHORIZED,
        title="Unauthorized",
        detail="X-Lockdin-Session-Token is missing, invalid, expired, or revoked",
        error_code="UNAUTHORIZED",
    )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=details.to_dict(),
    )


ActorDependency = Annotated[ActorContext, Depends(get_actor_context)]
