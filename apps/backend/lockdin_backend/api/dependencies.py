from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from lockdin_backend.identity import ActorContext, ActorContextError, actor_context_from_headers


def get_actor_context(
    user_id: Annotated[str | None, Header(alias="X-Lockdin-User-Id")] = None,
    device_id: Annotated[str | None, Header(alias="X-Lockdin-Device-Id")] = None,
    session_id: Annotated[str | None, Header(alias="X-Lockdin-Session-Id")] = None,
) -> ActorContext:
    try:
        return actor_context_from_headers(user_id, device_id, session_id)
    except ActorContextError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "https://lockdin.local/problems/actor-context-required",
                "title": "Actor context required",
                "status": status.HTTP_401_UNAUTHORIZED,
                "detail": str(exc),
            },
        ) from exc


ActorDependency = Annotated[ActorContext, Depends(get_actor_context)]
