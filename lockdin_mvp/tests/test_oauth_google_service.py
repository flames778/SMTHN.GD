import httpx

from app.services.oauth_google import GoogleOAuthService


class DummyResponse:
    def __init__(self, status_code: int, payload: dict) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self) -> dict:
        return self._payload


def test_exchange_code_returns_tokens_and_expiry(monkeypatch):
    def fake_post(*args, **kwargs):
        return DummyResponse(
            200,
            {
                "access_token": "g_access",
                "refresh_token": "g_refresh",
                "token_type": "Bearer",
                "scope": "scope-a scope-b",
                "expires_in": 3600,
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    service = GoogleOAuthService()

    result = service.exchange_code("sample-auth-code-12345")

    assert result["access_token"] == "g_access"
    assert result["refresh_token"] == "g_refresh"
    assert result["token_type"] == "Bearer"
    assert result["expires_at"] is not None


def test_refresh_token_reuses_refresh_token_value(monkeypatch):
    def fake_post(*args, **kwargs):
        return DummyResponse(
            200,
            {
                "access_token": "g_refreshed",
                "expires_in": 3000,
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    service = GoogleOAuthService()

    result = service.refresh_token("g_rt_existing")

    assert result["access_token"] == "g_refreshed"
    assert result["refresh_token"] == "g_rt_existing"
    assert result["expires_at"] is not None


def test_state_roundtrip_validation():
    service = GoogleOAuthService()
    state = service.generate_state("local-user")

    assert service.verify_state(state=state, user_id="local-user") is True
    assert service.verify_state(state=state, user_id="other-user") is False
