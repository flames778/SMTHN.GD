from app.db.session import SessionLocal
from app.repositories.events import EventRepository
from app.services.reminder_service import ReminderService
from app.workers.celery_app import celery_app


@celery_app.task(name="reminders.generate")
def generate_reminders() -> dict[str, int]:
    db = SessionLocal()
    try:
        events = EventRepository(db).list_upcoming()
        created = ReminderService(db).create_reminders_for_events(events)
        return {"events_seen": len(events), "reminders_created": created}
    finally:
        db.close()
