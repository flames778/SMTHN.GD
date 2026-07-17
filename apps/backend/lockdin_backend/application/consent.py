from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from lockdin_backend.domain.consent import ConsentRecord
from lockdin_backend.identity import ActorContext


class ConsentRepository(Protocol):
    def upsert(
        self,
        *,
        user_id: str,
        integration: str,
        data_category: str,
        purpose: str,
        granted: bool,
    ) -> ConsentRecord: ...


class UnitOfWork(Protocol):
    def commit(self) -> None: ...


@dataclass(frozen=True, slots=True)
class UpsertConsentCommand:
    integration: str
    data_category: str
    purpose: str
    granted: bool


class UpsertConsent:
    def __init__(self, repository: ConsentRepository, unit_of_work: UnitOfWork) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    def execute(self, actor: ActorContext, command: UpsertConsentCommand) -> ConsentRecord:
        record = self._repository.upsert(
            user_id=actor.user_id,
            integration=command.integration,
            data_category=command.data_category,
            purpose=command.purpose,
            granted=command.granted,
        )
        self._unit_of_work.commit()
        return record
