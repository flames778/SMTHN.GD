from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class IntegrationConnectRequest(BaseModel):
    provider: str = Field(default="google")
    auth_code: str
    redirect_uri: Optional[str] = None
    scope: str = "openid email profile https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/gmail.readonly"


class IntegrationAuthorizeUrlRequest(BaseModel):
    redirect_uri: Optional[str] = None
    scope: Optional[str] = None


class IntegrationAuthorizeUrlResponse(BaseModel):
    authorization_url: str
    state: str
    redirect_uri: str
    scope: str


class IntegrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    provider: str
    scope: str
    status: str
    token_type: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class GoogleSyncRequest(BaseModel):
    run_inline: bool = False


class GoogleSyncResponse(BaseModel):
    status: str
    task_id: Optional[str] = None
    stats: Optional[dict] = None
