from datetime import datetime
from typing import Any

from app.schemas.event import EventCreate


class GoogleCalendarConnector:
    source = "google_calendar"

    def normalize(self, raw_event: dict[str, Any]) -> EventCreate:
        # Google Calendar payloads can vary across API versions.
        start_raw = raw_event.get("start", {}).get("dateTime")
        end_raw = raw_event.get("end", {}).get("dateTime")

        if not start_raw:
            raise ValueError("Calendar event missing start.dateTime")

        meeting_url = raw_event.get("hangoutLink")
        if not meeting_url:
            description = raw_event.get("description", "")
            meeting_url = self._extract_meeting_url(description)

        return EventCreate(
            source=self.source,
            external_id=raw_event.get("id", ""),
            title=raw_event.get("summary", "Untitled event"),
            starts_at=datetime.fromisoformat(start_raw.replace("Z", "+00:00")),
            ends_at=datetime.fromisoformat(end_raw.replace("Z", "+00:00")) if end_raw else None,
            meeting_url=meeting_url,
            confidence=0.95,
            metadata={"provider": "google_calendar"},
        )

    @staticmethod
    def _extract_meeting_url(text: str) -> str | None:
        for token in text.split():
            if token.startswith("http://") or token.startswith("https://"):
                return token
        return None
