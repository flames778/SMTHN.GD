from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.consent import ConsentRepository
from app.schemas.consent import ConsentRead, ConsentUpsertRequest

router = APIRouter(prefix="/api/consent", tags=["consent"])

MVP_USER_ID = "local-user"


@router.post("", response_model=ConsentRead)
def upsert_consent(request: ConsentUpsertRequest, db: Session = Depends(get_db)) -> ConsentRead:
    row = ConsentRepository(db).upsert(
        user_id=MVP_USER_ID,
        integration=request.integration,
        data_category=request.data_category,
        purpose=request.purpose,
        granted=request.granted,
    )
    return ConsentRead.model_validate(row)


@router.get("", response_model=list[ConsentRead])
def list_consents(db: Session = Depends(get_db)) -> list[ConsentRead]:
    rows = ConsentRepository(db).list_for_user(user_id=MVP_USER_ID)
    return [ConsentRead.model_validate(row) for row in rows]


@router.delete("/{consent_id}")
def delete_consent(consent_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    deleted = ConsentRepository(db).delete(user_id=MVP_USER_ID, consent_id=consent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Consent record not found")

    return {"status": "deleted", "id": consent_id}
