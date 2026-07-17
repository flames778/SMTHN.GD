from datetime import UTC, datetime

from lockdin_backend.application.consent import UpsertConsent, UpsertConsentCommand
from lockdin_backend.domain.consent import ConsentRecord
from lockdin_backend.identity import ActorContext


class RecordingConsentRepository:
    def __init__(self) -> None:
        self.user_id: str | None = None

    def upsert(
        self,
        *,
        user_id: str,
        integration: str,
        data_category: str,
        purpose: str,
        granted: bool,
    ) -> ConsentRecord:
        self.user_id = user_id
        now = datetime.now(UTC)
        return ConsentRecord(
            id="consent-1",
            user_id=user_id,
            integration=integration,
            data_category=data_category,
            purpose=purpose,
            granted=granted,
            granted_at=now if granted else None,
            revoked_at=now if not granted else None,
            created_at=now,
            updated_at=now,
        )


class RecordingUnitOfWork:
    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


def test_upsert_consent_uses_actor_identity_and_commits_once() -> None:
    repository = RecordingConsentRepository()
    unit_of_work = RecordingUnitOfWork()
    use_case = UpsertConsent(repository, unit_of_work)

    result = use_case.execute(
        ActorContext(user_id="user-123"),
        UpsertConsentCommand(
            integration="google",
            data_category="calendar",
            purpose="meeting-preparation",
            granted=True,
        ),
    )

    assert repository.user_id == "user-123"
    assert result.user_id == "user-123"
    assert unit_of_work.commits == 1
