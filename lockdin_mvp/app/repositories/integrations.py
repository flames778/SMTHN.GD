from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import IntegrationTokenModel


class IntegrationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_google(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str,
        scope: str,
        token_type: str,
        expires_at: datetime | None,
    ) -> IntegrationTokenModel:
        existing = self.db.execute(
            select(IntegrationTokenModel).where(
                IntegrationTokenModel.user_id == user_id,
                IntegrationTokenModel.provider == "google",
            )
        ).scalar_one_or_none()

        if existing:
            existing.access_token = access_token
            existing.refresh_token = refresh_token
            existing.scope = scope
            existing.token_type = token_type
            existing.expires_at = expires_at
            existing.status = "connected"
            existing.updated_at = datetime.now(timezone.utc)
            self.db.add(existing)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        row = IntegrationTokenModel(
            user_id=user_id,
            provider="google",
            access_token=access_token,
            refresh_token=refresh_token,
            scope=scope,
            token_type=token_type,
            expires_at=expires_at,
            status="connected",
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_by_provider(self, user_id: str, provider: str) -> IntegrationTokenModel | None:
        return self.db.execute(
            select(IntegrationTokenModel).where(
                IntegrationTokenModel.user_id == user_id,
                IntegrationTokenModel.provider == provider,
            )
        ).scalar_one_or_none()

    def list_for_user(self, user_id: str) -> list[IntegrationTokenModel]:
        result = self.db.execute(
            select(IntegrationTokenModel)
            .where(IntegrationTokenModel.user_id == user_id)
            .order_by(IntegrationTokenModel.updated_at.desc())
        )
        return list(result.scalars().all())

    def update_tokens(
        self,
        row: IntegrationTokenModel,
        access_token: str,
        refresh_token: str,
        expires_at: datetime | None,
    ) -> IntegrationTokenModel:
        row.access_token = access_token
        row.refresh_token = refresh_token
        row.expires_at = expires_at
        row.status = "connected"
        row.updated_at = datetime.now(timezone.utc)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def revoke(self, row: IntegrationTokenModel) -> IntegrationTokenModel:
        row.status = "revoked"
        row.access_token = ""
        row.refresh_token = ""
        row.updated_at = datetime.now(timezone.utc)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
