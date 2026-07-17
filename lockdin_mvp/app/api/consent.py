from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from lockdin_backend.api.dependencies import ActorDependency
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.consent import ConsentRepository
from app.schemas.consent import ConsentRead, ConsentUpsertRequest
from app.schemas.problem_details import problem_details

router = APIRouter(prefix="/api/consent", tags=["consent"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=ConsentRead)
def upsert_consent(request: ConsentUpsertRequest, actor: ActorDependency, db: DbSession) -> ConsentRead:
    row = ConsentRepository(db).upsert(
        user_id=actor.user_id,
        integration=request.integration,
        data_category=request.data_category,
        purpose=request.purpose,
        granted=request.granted,
    )
    return ConsentRead.model_validate(row)


@router.get("", response_model=list[ConsentRead])
def list_consents(actor: ActorDependency, db: DbSession) -> list[ConsentRead]:
    rows = ConsentRepository(db).list_for_user(user_id=actor.user_id)
    return [ConsentRead.model_validate(row) for row in rows]


@router.delete("/{consent_id}")
def delete_consent(consent_id: str, actor: ActorDependency, db: DbSession) -> dict[str, str]:
    deleted = ConsentRepository(db).delete(user_id=actor.user_id, consent_id=consent_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=problem_details(
                error_code="CONSENT_RECORD_NOT_FOUND",
                detail="Consent record not found",
            ).to_dict(),
        )

    return {"status": "deleted", "id": consent_id}
