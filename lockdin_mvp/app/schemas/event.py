from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    source: str
    external_id: str
    title: str
    starts_at: datetime
    ends_at: Optional[datetime] = None
    meeting_url: Optional[str] = None
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EventRead(EventCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
