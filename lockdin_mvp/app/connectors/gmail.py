from datetime import datetime, timezone
from typing import Any

from app.schemas.event import EventCreate


class GmailConnector:
    source = "gmail"

    def normalize(self, raw_message: dict[str, Any]) -> EventCreate:
        payload = raw_message.get("payload", {})
        headers = payload.get("headers", [])

        subject = self._header_value(headers, "Subject") or "Email event"
        external_id = raw_message.get("id", "")
        meeting_url = self._extract_meeting_url(raw_message.get("snippet", ""))

        internal_ts = raw_message.get("internalDate")
        if internal_ts:
            starts_at = datetime.fromtimestamp(int(internal_ts) / 1000, tz=timezone.utc)
        else:
            starts_at = datetime.now(tz=timezone.utc)

        return EventCreate(
            source=self.source,
            external_id=external_id,
            title=subject,
            starts_at=starts_at,
            meeting_url=meeting_url,
            confidence=0.75,
            metadata={"provider": "gmail", "from": self._header_value(headers, "From")},
        )

    @staticmethod
    def _header_value(headers: list[dict[str, str]], name: str) -> str | None:
        lowered = name.lower()
        for header in headers:
            if header.get("name", "").lower() == lowered:
                return header.get("value")
        return None

    @staticmethod
    def _extract_meeting_url(text: str) -> str | None:
        for token in text.split():
            if token.startswith("http://") or token.startswith("https://"):
                return token
        return None
