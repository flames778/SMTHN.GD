from datetime import UTC, datetime, timedelta

import pytest
from lockdin_backend.persistence.base import Base
from lockdin_backend.persistence.identity import (
    BootstrapAlreadyCompletedError,
    IdentityRepository,
)
from lockdin_backend.persistence.models import SessionModel
from lockdin_backend.security.session_tokens import hash_session_token
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


@pytest.fixture
def db() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_bootstrap_hashes_token_and_resolves_owning_actor(db: Session) -> None:
    repository = IdentityRepository(db)

    issued = repository.bootstrap_first_user(
        display_name="Owner",
        device_name="Workstation",
        platform="windows",
    )
    stored_session = db.scalar(select(SessionModel))

    assert stored_session is not None
    assert stored_session.token_hash == hash_session_token(issued.token)
    assert stored_session.token_hash != issued.token

    actor = repository.resolve_actor(issued.token)
    assert actor is not None
    assert actor.user_id == issued.user_id
    assert actor.device_id == issued.device_id
    assert actor.session_id == issued.session_id


def test_bootstrap_can_only_create_the_first_user(db: Session) -> None:
    repository = IdentityRepository(db)
    repository.bootstrap_first_user(
        display_name="Owner",
        device_name="Workstation",
        platform="windows",
    )

    with pytest.raises(BootstrapAlreadyCompletedError, match="already complete"):
        repository.bootstrap_first_user(
            display_name="Second Owner",
            device_name="Other Device",
            platform="windows",
        )


def test_expired_and_revoked_sessions_do_not_resolve(db: Session) -> None:
    repository = IdentityRepository(db)
    issued = repository.bootstrap_first_user(
        display_name="Owner",
        device_name="Workstation",
        platform="windows",
        ttl=timedelta(minutes=5),
    )

    assert (
        repository.resolve_actor(
            issued.token,
            now=datetime.now(UTC) + timedelta(minutes=6),
        )
        is None
    )
    assert repository.revoke_session(issued.session_id)
    assert repository.resolve_actor(issued.token) is None
