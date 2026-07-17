from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ConsentRecord:
    id: str
    user_id: str
    integration: str
    data_category: str
    purpose: str
    granted: bool
    granted_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    updated_at: datetime
