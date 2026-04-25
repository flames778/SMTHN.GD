from app.db.session import SessionLocal
from app.repositories.consent import ConsentRepository
from app.repositories.events import EventRepository
from app.repositories.integrations import IntegrationRepository
from app.services.integration_sync_service import IntegrationSyncService
from app.services.reminder_service import ReminderService
from app.workers.celery_app import celery_app

MVP_USER_ID = "local-user"


@celery_app.task(name="reminders.generate")
def generate_reminders() -> dict[str, int]:
    db = SessionLocal()
    try:
        events = EventRepository(db).list_upcoming()
        created = ReminderService(db).create_reminders_for_events(events)
        return {"events_seen": len(events), "reminders_created": created}
    finally:
        db.close()


@celery_app.task(name="integrations.sync_google")
def sync_google_integrations() -> dict[str, int | str]:
    db = SessionLocal()
    try:
        integration_repo = IntegrationRepository(db)
        consent_repo = ConsentRepository(db)
        integration = integration_repo.get_by_provider(user_id=MVP_USER_ID, provider="google")
        if not integration or integration.status != "connected" or not integration.access_token:
            return {"status": "skipped", "reason": "google integration not connected", "calendar": 0, "gmail": 0}

        sync_service = IntegrationSyncService(db)
        calendar_count = 0
        gmail_count = 0

        if consent_repo.is_granted(
            user_id=MVP_USER_ID,
            integration="google",
            data_category="calendar",
            purpose="sync",
        ):
            calendar_count = sync_service.sync_google_calendar(integration.access_token)

        if consent_repo.is_granted(
            user_id=MVP_USER_ID,
            integration="google",
            data_category="gmail",
            purpose="sync",
        ):
            gmail_count = sync_service.sync_gmail(integration.access_token)

        return {"status": "ok", "calendar": calendar_count, "gmail": gmail_count}
    finally:
        db.close()
