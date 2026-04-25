from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json
from secrets import token_urlsafe
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings


class GoogleOAuthService:
    """Google OAuth service for token exchange and refresh."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @staticmethod
    def _normalize_expiry(expires_in: int | None) -> datetime:
        ttl_seconds = expires_in if expires_in and expires_in > 0 else 3300
        return datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    @staticmethod
    def _b64url_encode(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

    @staticmethod
    def _b64url_decode(raw: str) -> bytes:
        padding = "=" * (-len(raw) % 4)
        return base64.urlsafe_b64decode(raw + padding)

    def _sign(self, payload: bytes) -> str:
        digest = hmac.new(
            self.settings.app_encryption_key.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).digest()
        return self._b64url_encode(digest)

    def generate_state(self, user_id: str) -> str:
        state_payload = {
            "u": user_id,
            "n": token_urlsafe(10),
            "iat": int(datetime.now(timezone.utc).timestamp()),
        }
        payload_bytes = json.dumps(state_payload, separators=(",", ":")).encode("utf-8")
        return f"{self._b64url_encode(payload_bytes)}.{self._sign(payload_bytes)}"

    def verify_state(self, state: str, user_id: str, max_age_seconds: int = 600) -> bool:
        try:
            payload_b64, sig = state.split(".", maxsplit=1)
            payload_bytes = self._b64url_decode(payload_b64)
            expected = self._sign(payload_bytes)
            if not hmac.compare_digest(sig, expected):
                return False

            payload = json.loads(payload_bytes.decode("utf-8"))
            issued = int(payload.get("iat", 0))
            if payload.get("u") != user_id:
                return False
            now_ts = int(datetime.now(timezone.utc).timestamp())
            if now_ts - issued > max_age_seconds:
                return False
            return True
        except Exception:
            return False

    def build_authorize_url(self, user_id: str, redirect_uri: str | None = None, scope: str | None = None) -> dict:
        resolved_redirect_uri = redirect_uri or self.settings.google_oauth_default_redirect_uri
        resolved_scope = scope or (
            "openid email profile "
            "https://www.googleapis.com/auth/calendar.readonly "
            "https://www.googleapis.com/auth/gmail.readonly"
        )
        state = self.generate_state(user_id)
        query = urlencode(
            {
                "client_id": self.settings.google_client_id,
                "redirect_uri": resolved_redirect_uri,
                "response_type": "code",
                "scope": resolved_scope,
                "access_type": "offline",
                "prompt": "consent",
                "state": state,
            }
        )
        return {
            "authorization_url": f"{self.settings.google_oauth_authorize_url}?{query}",
            "state": state,
            "redirect_uri": resolved_redirect_uri,
            "scope": resolved_scope,
        }

    def exchange_code(self, auth_code: str, redirect_uri: str | None = None) -> dict:
        if len(auth_code.strip()) < 8:
            raise ValueError("auth_code appears invalid")

        payload = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "client_id": self.settings.google_client_id,
            "client_secret": self.settings.google_client_secret,
            "redirect_uri": redirect_uri or self.settings.google_oauth_default_redirect_uri,
        }

        try:
            response = httpx.post(self.settings.google_oauth_token_url, data=payload, timeout=15.0)
        except httpx.HTTPError as exc:
            raise ValueError(f"Google token exchange failed: {exc}") from exc

        if response.status_code >= 400:
            raise ValueError(f"Google token exchange failed: {response.text}")

        token = response.json()

        return {
            "access_token": token.get("access_token", ""),
            "refresh_token": token.get("refresh_token", ""),
            "token_type": token.get("token_type", "Bearer"),
            "scope": token.get("scope", ""),
            "expires_at": self._normalize_expiry(token.get("expires_in")),
        }

    def refresh_token(self, refresh_token: str) -> dict:
        if not refresh_token:
            raise ValueError("Missing refresh token")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.settings.google_client_id,
            "client_secret": self.settings.google_client_secret,
        }

        try:
            response = httpx.post(self.settings.google_oauth_token_url, data=payload, timeout=15.0)
        except httpx.HTTPError as exc:
            raise ValueError(f"Google token refresh failed: {exc}") from exc

        if response.status_code >= 400:
            raise ValueError(f"Google token refresh failed: {response.text}")

        token = response.json()

        return {
            "access_token": token.get("access_token", ""),
            "refresh_token": token.get("refresh_token", refresh_token),
            "expires_at": self._normalize_expiry(token.get("expires_in")),
        }
