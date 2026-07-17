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
