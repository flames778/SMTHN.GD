import pytest
from lockdin_backend.identity import ActorContextError, actor_context_from_headers


def test_actor_context_requires_user_identity() -> None:
    with pytest.raises(ActorContextError, match="header is required"):
        actor_context_from_headers(None)


def test_actor_context_rejects_blank_user_identity() -> None:
    with pytest.raises(ActorContextError, match="must not be blank"):
        actor_context_from_headers("   ")


def test_actor_context_preserves_request_identity() -> None:
    actor = actor_context_from_headers(" user-123 ", " device-1 ", " session-9 ")

    assert actor.user_id == "user-123"
    assert actor.device_id == "device-1"
    assert actor.session_id == "session-9"
