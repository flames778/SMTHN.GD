from app.db.session import SessionLocal
from app.repositories.consent import ConsentRepository
from app.repositories.events import EventRepository
from app.repositories.integrations import IntegrationRepository
from app.services.integration_sync_service import IntegrationSyncService
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


@celery_app.task(name="integrations.sync_google")
def sync_google_integrations(user_id: str) -> dict[str, int | str]:
    db = SessionLocal()
    try:
        integration_repo = IntegrationRepository(db)
        consent_repo = ConsentRepository(db)
        integration = integration_repo.get_by_provider(user_id=user_id, provider="google")
        if not integration or integration.status != "connected":
            return {"status": "skipped", "reason": "google integration not connected", "calendar": 0, "gmail": 0}

        tokens = integration_repo.get_decrypted_tokens(integration)
        if not tokens["access_token"]:
            return {"status": "skipped", "reason": "access token not available", "calendar": 0, "gmail": 0}

        sync_service = IntegrationSyncService(db)
        calendar_count = 0
        gmail_count = 0

        if consent_repo.is_granted(
            user_id=user_id,
            integration="google",
            data_category="calendar",
            purpose="sync",
        ):
            calendar_count = sync_service.sync_google_calendar(tokens["access_token"])

        if consent_repo.is_granted(
            user_id=user_id,
            integration="google",
            data_category="gmail",
            purpose="sync",
        ):
            gmail_count = sync_service.sync_gmail(tokens["access_token"])

        return {"status": "ok", "calendar": calendar_count, "gmail": gmail_count}
    finally:
        db.close()
