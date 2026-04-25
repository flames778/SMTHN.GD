from datetime import datetime, timedelta, timezone

from app.connectors.google_calendar import GoogleCalendarConnector
from app.services.reminder_service import ReminderService


class DummyEvent:
    def __init__(self, event_id: str, title: str, starts_at: datetime) -> None:
        self.id = event_id
        self.title = title
        self.starts_at = starts_at


class DummyReminders:
    def __init__(self) -> None:
        self.rows = []

    def create(self, data):
        self.rows.append(data)
        return data


def test_google_calendar_normalization_extracts_fields():
    connector = GoogleCalendarConnector()
    raw = {
        "id": "evt_123",
        "summary": "Team Sync",
        "start": {"dateTime": "2026-04-25T10:00:00Z"},
        "end": {"dateTime": "2026-04-25T10:30:00Z"},
        "hangoutLink": "https://meet.google.com/abc-defg-hij",
    }

    event = connector.normalize(raw)

    assert event.source == "google_calendar"
    assert event.external_id == "evt_123"
    assert event.title == "Team Sync"
    assert event.meeting_url == "https://meet.google.com/abc-defg-hij"


def test_reminder_service_creates_only_upcoming_items():
    now = datetime.now(timezone.utc)
    near = DummyEvent("1", "Near Meeting", now + timedelta(minutes=5))
    far = DummyEvent("2", "Far Meeting", now + timedelta(minutes=60))

    service = ReminderService(db=None, lead_minutes=10)
    fake_repo = DummyReminders()
    service.reminders = fake_repo

    count = service.create_reminders_for_events([near, far])

    assert count == 1
    assert len(fake_repo.rows) == 1
    assert fake_repo.rows[0].event_id == "1"
