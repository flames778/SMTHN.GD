from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ConsentUpsertRequest(BaseModel):
    integration: str
    data_category: str
    purpose: str
    granted: bool


class ConsentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    integration: str
    data_category: str
    purpose: str
    granted: bool
    granted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
