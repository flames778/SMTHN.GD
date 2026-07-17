from dataclasses import FrozenInstanceError

import pytest
from lockdin_backend.identity import ActorContext, ActorContextError


def test_actor_context_rejects_blank_user_identity() -> None:
    with pytest.raises(ActorContextError, match="must not be blank"):
        ActorContext(user_id="   ")


def test_actor_context_preserves_resolved_identity() -> None:
    actor = ActorContext(user_id="user-123", device_id="device-1", session_id="session-9")

    assert actor.user_id == "user-123"
    assert actor.device_id == "device-1"
    assert actor.session_id == "session-9"


def test_actor_context_is_immutable() -> None:
    actor = ActorContext(user_id="user-123")

    with pytest.raises(FrozenInstanceError):
        actor.user_id = "other-user"  # type: ignore[misc]
