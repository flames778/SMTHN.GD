from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.connectors.gmail import GmailConnector
from app.connectors.google_calendar import GoogleCalendarConnector
from app.repositories.events import EventRepository


class IntegrationSyncService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.events = EventRepository(db)
        self.calendar_connector = GoogleCalendarConnector()
        self.gmail_connector = GmailConnector()

    @staticmethod
    def _auth_headers(access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}"}

    def fetch_google_calendar_events(self, access_token: str, max_results: int = 25) -> list[dict]:
        params = {
            "singleEvents": "true",
            "orderBy": "startTime",
            "timeMin": datetime.now(timezone.utc).isoformat(),
            "maxResults": str(max_results),
        }
        response = httpx.get(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers=self._auth_headers(access_token),
            params=params,
            timeout=20.0,
        )
        if response.status_code >= 400:
            raise ValueError(f"Calendar sync failed: {response.text}")
        payload = response.json()
        return payload.get("items", [])

    def fetch_gmail_messages(self, access_token: str, max_results: int = 10) -> list[dict]:
        response = httpx.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers=self._auth_headers(access_token),
            params={"maxResults": str(max_results)},
            timeout=20.0,
        )
        if response.status_code >= 400:
            raise ValueError(f"Gmail list sync failed: {response.text}")
        payload = response.json()
        return payload.get("messages", [])

    def fetch_gmail_message(self, access_token: str, message_id: str) -> dict:
        response = httpx.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
            headers=self._auth_headers(access_token),
            params={"format": "full"},
            timeout=20.0,
        )
        if response.status_code >= 400:
            raise ValueError(f"Gmail message sync failed: {response.text}")
        return response.json()

    def sync_google_calendar(self, access_token: str) -> int:
        raw_events = self.fetch_google_calendar_events(access_token)
        saved = 0
        for raw_event in raw_events:
            normalized = self.calendar_connector.normalize(raw_event)
            self.events.upsert(normalized)
            saved += 1
        return saved

    def sync_gmail(self, access_token: str) -> int:
        raw_messages = self.fetch_gmail_messages(access_token)
        saved = 0
        for message in raw_messages:
            message_id = message.get("id")
            if not message_id:
                continue
            full_message = self.fetch_gmail_message(access_token, message_id)
            normalized = self.gmail_connector.normalize(full_message)
            self.events.upsert(normalized)
            saved += 1
        return saved
