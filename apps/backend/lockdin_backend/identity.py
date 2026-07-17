from __future__ import annotations

from dataclasses import dataclass


class ActorContextError(ValueError):
    """Raised when request identity cannot produce a valid actor context."""


@dataclass(frozen=True, slots=True)
class ActorContext:
    user_id: str
    device_id: str | None = None
    session_id: str | None = None

    def __post_init__(self) -> None:
        if not self.user_id.strip():
            raise ActorContextError("user_id must not be blank")


def actor_context_from_headers(
    user_id: str | None,
    device_id: str | None = None,
    session_id: str | None = None,
) -> ActorContext:
    if user_id is None:
        raise ActorContextError("X-Lockdin-User-Id header is required")

    return ActorContext(
        user_id=user_id.strip(),
        device_id=device_id.strip() if device_id else None,
        session_id=session_id.strip() if session_id else None,
    )
