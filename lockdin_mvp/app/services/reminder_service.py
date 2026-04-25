from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.models import EventModel
from app.repositories.reminders import ReminderRepository
from app.schemas.task_suggestion import TaskSuggestionCreate


class ReminderService:
    def __init__(self, db: Session, lead_minutes: int = 10) -> None:
        self.db = db
        self.lead_minutes = lead_minutes
        self.reminders = ReminderRepository(db)

    def create_reminders_for_events(self, events: list[EventModel]) -> int:
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(minutes=self.lead_minutes)
        created = 0

        for event in events:
            starts_at = event.starts_at
            if starts_at.tzinfo is None:
                starts_at = starts_at.replace(tzinfo=timezone.utc)

            if now <= starts_at <= cutoff:
                self.reminders.create(
                    TaskSuggestionCreate(
                        event_id=event.id,
                        title=f"Prepare for: {event.title}",
                        reason="Meeting starts soon",
                        urgency=3,
                        status="pending",
                    )
                )
                created += 1

        return created
