from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import TaskSuggestionModel
from app.schemas.task_suggestion import TaskSuggestionCreate


class ReminderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: TaskSuggestionCreate) -> TaskSuggestionModel:
        row = TaskSuggestionModel(
            event_id=data.event_id,
            title=data.title,
            reason=data.reason,
            urgency=data.urgency,
            status=data.status,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_all(self) -> list[TaskSuggestionModel]:
        result = self.db.execute(select(TaskSuggestionModel).order_by(TaskSuggestionModel.created_at.desc()))
        return list(result.scalars().all())
