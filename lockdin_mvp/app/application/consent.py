"""Consent use cases: upsert, list, delete consent records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from lockdin_backend.identity import ActorContext


# --------------------------------------------------------------------------- #
# Domain result type
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class ConsentResult:
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


# --------------------------------------------------------------------------- #
# Repository and UoW protocols
# --------------------------------------------------------------------------- #

class ConsentRow(Protocol):
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


class ConsentRepository(Protocol):
    def upsert(
        self,
        *,
        user_id: str,
        integration: str,
        data_category: str,
        purpose: str,
        granted: bool,
    ) -> ConsentRow: ...

    def list_for_user(self, user_id: str) -> list[ConsentRow]: ...

    def delete(self, user_id: str, consent_id: str) -> bool: ...


class UnitOfWork(Protocol):
    def commit(self) -> None: ...


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class UpsertConsentCommand:
    integration: str
    data_category: str
    purpose: str
    granted: bool


@dataclass(frozen=True, slots=True)
class DeleteConsentCommand:
    consent_id: str


# --------------------------------------------------------------------------- #
# Custom exceptions
# --------------------------------------------------------------------------- #

class ConsentNotFoundError(Exception):
    def __init__(self, consent_id: str) -> None:
        super().__init__(f"Consent record '{consent_id}' not found")
        self.consent_id = consent_id


# --------------------------------------------------------------------------- #
# Use cases
# --------------------------------------------------------------------------- #

def _row_to_result(row: ConsentRow) -> ConsentResult:
    return ConsentResult(
        id=row.id,
        user_id=row.user_id,
        integration=row.integration,
        data_category=row.data_category,
        purpose=row.purpose,
        granted=row.granted,
        granted_at=row.granted_at,
        revoked_at=row.revoked_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class UpsertConsent:
    """Upsert a consent record for the current actor.

    Owns the transaction boundary.
    """

    def __init__(self, repository: ConsentRepository, unit_of_work: UnitOfWork) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    def execute(self, actor: ActorContext, command: UpsertConsentCommand) -> ConsentResult:
        row = self._repository.upsert(
            user_id=actor.user_id,
            integration=command.integration,
            data_category=command.data_category,
            purpose=command.purpose,
            granted=command.granted,
        )
        self._unit_of_work.commit()
        return _row_to_result(row)


class ListConsents:
    """List all consent records for the current actor."""

    def __init__(self, repository: ConsentRepository) -> None:
        self._repository = repository

    def execute(self, actor: ActorContext) -> list[ConsentResult]:
        rows = self._repository.list_for_user(actor.user_id)
        return [_row_to_result(row) for row in rows]


class DeleteConsent:
    """Delete a consent record owned by the current actor.

    Raises ConsentNotFoundError if the record does not exist or is not owned by the actor.
    Owns the transaction boundary.
    """

    def __init__(self, repository: ConsentRepository, unit_of_work: UnitOfWork) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    def execute(self, actor: ActorContext, command: DeleteConsentCommand) -> None:
        deleted = self._repository.delete(actor.user_id, command.consent_id)
        if not deleted:
            raise ConsentNotFoundError(command.consent_id)
        self._unit_of_work.commit()
