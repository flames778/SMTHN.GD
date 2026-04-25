from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskSuggestionCreate(BaseModel):
    event_id: str
    title: str
    reason: str
    urgency: int = Field(default=1, ge=1, le=3)
    status: str = "pending"


class TaskSuggestionRead(TaskSuggestionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
