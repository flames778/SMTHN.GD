from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import EventModel
from app.schemas.event import EventCreate


class EventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert(self, data: EventCreate) -> EventModel:
        existing = self.db.execute(
            select(EventModel).where(
                EventModel.source == data.source,
                EventModel.external_id == data.external_id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.title = data.title
            existing.starts_at = data.starts_at
            existing.ends_at = data.ends_at
            existing.meeting_url = data.meeting_url
            existing.confidence = data.confidence
            self.db.add(existing)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        event = EventModel(
            source=data.source,
            external_id=data.external_id,
            title=data.title,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
            meeting_url=data.meeting_url,
            confidence=data.confidence,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_upcoming(self) -> list[EventModel]:
        result = self.db.execute(select(EventModel).order_by(EventModel.starts_at.asc()))
        return list(result.scalars().all())
