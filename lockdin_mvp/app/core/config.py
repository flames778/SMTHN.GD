from functools import lru_cache

from pydantic import Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")
    app_encryption_key: str = Field(alias="APP_ENCRYPTION_KEY")

    google_client_id: str = Field(default="", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", alias="GOOGLE_CLIENT_SECRET")
    google_oauth_token_url: str = Field(
        default="https://oauth2.googleapis.com/token",
        alias="GOOGLE_OAUTH_TOKEN_URL",
    )
    google_oauth_authorize_url: str = Field(
        default="https://accounts.google.com/o/oauth2/v2/auth",
        alias="GOOGLE_OAUTH_AUTHORIZE_URL",
    )
    google_oauth_default_redirect_uri: str = Field(
        default="http://localhost:3000/oauth/google/callback",
        alias="GOOGLE_OAUTH_DEFAULT_REDIRECT_URI",
    )

    stepfun_api_key: str = Field(default="", alias="STEPFUN_API_KEY")
    nemotron_api_key: str = Field(default="", alias="NEMOTRON_API_KEY")

    @model_validator(mode="after")
    def validate_encryption_key(self) -> "Settings":
        if len(self.app_encryption_key.strip()) < 32:
            raise ValueError("APP_ENCRYPTION_KEY must be at least 32 characters")
        return self

    def validate_startup_config(self) -> None:
        missing = []
        if not self.google_client_id:
            missing.append("GOOGLE_CLIENT_ID")
        if not self.google_client_secret:
            missing.append("GOOGLE_CLIENT_SECRET")

        if missing:
            missing_str = ", ".join(missing)
            raise RuntimeError(
                f"Missing required integration configuration: {missing_str}. "
                "Set these in your .env before startup."
            )


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        raise RuntimeError(f"Invalid startup configuration: {exc}") from exc
