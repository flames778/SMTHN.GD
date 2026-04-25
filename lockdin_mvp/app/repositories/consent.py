from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ConsentRecordModel


class ConsentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert(
        self,
        user_id: str,
        integration: str,
        data_category: str,
        purpose: str,
        granted: bool,
    ) -> ConsentRecordModel:
        existing = self.db.execute(
            select(ConsentRecordModel).where(
                ConsentRecordModel.user_id == user_id,
                ConsentRecordModel.integration == integration,
                ConsentRecordModel.data_category == data_category,
                ConsentRecordModel.purpose == purpose,
            )
        ).scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if existing:
            existing.granted = granted
            existing.granted_at = now if granted else existing.granted_at
            existing.revoked_at = now if not granted else None
            existing.updated_at = now
            self.db.add(existing)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        row = ConsentRecordModel(
            user_id=user_id,
            integration=integration,
            data_category=data_category,
            purpose=purpose,
            granted=granted,
            granted_at=now if granted else None,
            revoked_at=now if not granted else None,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_for_user(self, user_id: str) -> list[ConsentRecordModel]:
        result = self.db.execute(
            select(ConsentRecordModel)
            .where(ConsentRecordModel.user_id == user_id)
            .order_by(ConsentRecordModel.updated_at.desc())
        )
        return list(result.scalars().all())

    def is_granted(self, user_id: str, integration: str, data_category: str, purpose: str) -> bool:
        row = self.db.execute(
            select(ConsentRecordModel).where(
                ConsentRecordModel.user_id == user_id,
                ConsentRecordModel.integration == integration,
                ConsentRecordModel.data_category == data_category,
                ConsentRecordModel.purpose == purpose,
            )
        ).scalar_one_or_none()
        return bool(row and row.granted)

    def delete(self, user_id: str, consent_id: str) -> bool:
        row = self.db.execute(
            select(ConsentRecordModel).where(
                ConsentRecordModel.user_id == user_id,
                ConsentRecordModel.id == consent_id,
            )
        ).scalar_one_or_none()

        if not row:
            return False

        self.db.delete(row)
        self.db.commit()
        return True
