"""Consent API routes - thin layer over application use cases."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from lockdin_backend.api.dependencies import ActorDependency
from sqlalchemy.orm import Session

from app.application.consent import (
    ConsentNotFoundError,
    DeleteConsent,
    DeleteConsentCommand,
    ListConsents,
    UpsertConsent,
    UpsertConsentCommand,
)
from app.db.session import get_db
from app.repositories.consent import ConsentRepository
from app.schemas.consent import ConsentRead, ConsentUpsertRequest
from app.schemas.problem_details import problem_details

router = APIRouter(prefix="/api/consent", tags=["consent"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=ConsentRead)
def upsert_consent(request: ConsentUpsertRequest, actor: ActorDependency, db: DbSession) -> ConsentRead:
    use_case = UpsertConsent(repository=ConsentRepository(db), unit_of_work=db)
    result = use_case.execute(
        actor,
        UpsertConsentCommand(
            integration=request.integration,
            data_category=request.data_category,
            purpose=request.purpose,
            granted=request.granted,
        ),
    )
    return ConsentRead.model_validate(result)


@router.get("", response_model=list[ConsentRead])
def list_consents(actor: ActorDependency, db: DbSession) -> list[ConsentRead]:
    use_case = ListConsents(repository=ConsentRepository(db))
    results = use_case.execute(actor)
    return [ConsentRead.model_validate(r) for r in results]


@router.delete("/{consent_id}")
def delete_consent(consent_id: str, actor: ActorDependency, db: DbSession) -> dict[str, str]:
    use_case = DeleteConsent(repository=ConsentRepository(db), unit_of_work=db)
    try:
        use_case.execute(actor, DeleteConsentCommand(consent_id=consent_id))
    except ConsentNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=problem_details(
                error_code="CONSENT_RECORD_NOT_FOUND",
                detail="Consent record not found",
            ).to_dict(),
        ) from exc
    return {"status": "deleted", "id": consent_id}
