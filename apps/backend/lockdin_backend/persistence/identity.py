from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from lockdin_backend.identity import ActorContext
from lockdin_backend.persistence.models import DeviceModel, SessionModel, UserModel
from lockdin_backend.security.session_tokens import generate_session_token, hash_session_token


class BootstrapAlreadyCompletedError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class IssuedSession:
    user_id: str
    device_id: str
    session_id: str
    token: str
    expires_at: datetime


class IdentityRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def bootstrap_first_user(
        self,
        *,
        display_name: str,
        device_name: str,
        platform: str,
        ttl: timedelta = timedelta(days=30),
    ) -> IssuedSession:
        user_count = self._db.scalar(select(func.count()).select_from(UserModel))
        if user_count:
            raise BootstrapAlreadyCompletedError("initial user bootstrap is already complete")

        try:
            user = UserModel(display_name=display_name.strip(), bootstrap_slot="initial-owner")
            self._db.add(user)
            self._db.flush()

            device = DeviceModel(
                user_id=user.id, name=device_name.strip(), platform=platform.strip()
            )
            self._db.add(device)
            self._db.flush()

            token = generate_session_token()
            expires_at = datetime.now(UTC) + ttl
            session = SessionModel(
                user_id=user.id,
                device_id=device.id,
                token_hash=hash_session_token(token),
                expires_at=expires_at,
            )
            self._db.add(session)
            self._db.commit()
        except IntegrityError as exc:
            self._db.rollback()
            raise BootstrapAlreadyCompletedError(
                "initial user bootstrap is already complete"
            ) from exc

        return IssuedSession(
            user_id=user.id,
            device_id=device.id,
            session_id=session.id,
            token=token,
            expires_at=expires_at,
        )

    def resolve_actor(self, token: str, *, now: datetime | None = None) -> ActorContext | None:
        checked_at = now or datetime.now(UTC)
        session = self._db.scalar(
            select(SessionModel).where(SessionModel.token_hash == hash_session_token(token))
        )
        if session is None or session.revoked_at is not None:
            return None

        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= checked_at:
            return None

        user_status = self._db.scalar(
            select(UserModel.status).where(UserModel.id == session.user_id)
        )
        if user_status != "active":
            return None

        session.last_seen_at = checked_at
        self._db.commit()
        return ActorContext(
            user_id=session.user_id,
            device_id=session.device_id,
            session_id=session.id,
        )

    def revoke_session(self, session_id: str, *, revoked_at: datetime | None = None) -> bool:
        session = self._db.get(SessionModel, session_id)
        if session is None:
            return False
        session.revoked_at = revoked_at or datetime.now(UTC)
        self._db.commit()
        return True
