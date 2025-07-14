from sqlalchemy.orm import Session
from smart_scheduler.models import Deadline, DeadlineType, DeadlineRecurrence
from datetime import datetime, timedelta
from typing import List, Optional

class DeadlineService:
    def __init__(self, db: Session):
        self.db = db

    def get_deadline(self, deadline_id: int) -> Optional[Deadline]:
        return self.db.query(Deadline).filter(Deadline.id == deadline_id).first()

    def get_deadlines(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, completed: Optional[bool] = None) -> List[Deadline]:
        query = self.db.query(Deadline)
        if start_date:
            query = query.filter(Deadline.due_date >= start_date)
        if end_date:
            query = query.filter(Deadline.due_date <= end_date)
        if completed is not None:
            query = query.filter(Deadline.completed == completed)
        return query.order_by(Deadline.due_date).all()

    def get_deadlines_plain(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, completed: Optional[bool] = None):
        # Returns list of dicts for analytics
        deadlines = self.get_deadlines(start_date, end_date, completed)
        return [
            {
                "id": d.id,
                "completed": bool(d.completed),
                "due_date": d.due_date,
                "type": d.type.value if hasattr(d.type, 'value') else str(d.type)
            }
            for d in deadlines
        ]

    def get_deadlines_plain_range(self, start_date=None, end_date=None):
        from datetime import timezone
        deadlines = self.get_deadlines()
        result = []
        # Ensure start_date and end_date are offset-aware (UTC)
        if start_date and start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date and end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        for d in deadlines:
            due_date = getattr(d, 'due_date', None)
            if due_date is not None and due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)
            if due_date is not None and (not start_date or due_date >= start_date) and (not end_date or due_date <= end_date):
                result.append({
                    "id": d.id,
                    "title": d.title,
                    "due_date": d.due_date,
                    "color": d.color,
                    "completed": bool(d.completed),
                    "project_id": d.project_id,
                    "recurrence": d.recurrence.value if hasattr(d.recurrence, 'value') else str(d.recurrence)
                })
        return result

    def create_deadline(self, title: str, due_date: datetime, description: Optional[str] = None, type: DeadlineType = DeadlineType.GENERAL, color: Optional[str] = None, recurrence: DeadlineRecurrence = DeadlineRecurrence.NONE, recurrence_end_date: Optional[datetime] = None, task_id: Optional[int] = None, project_id: Optional[int] = None) -> Deadline:
        deadline = Deadline(
            title=title,
            due_date=due_date,
            description=description,
            type=type,
            color=color or "#EF4444",
            recurrence=recurrence,
            recurrence_end_date=recurrence_end_date,
            task_id=task_id,
            project_id=project_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(deadline)
        self.db.commit()
        self.db.refresh(deadline)
        return deadline

    def update_deadline(self, deadline_id: int, **kwargs) -> Optional[Deadline]:
        deadline = self.get_deadline(deadline_id)
        if not deadline:
            return None
        for key, value in kwargs.items():
            if hasattr(deadline, key):
                setattr(deadline, key, value)
        deadline.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(deadline)
        return deadline

    def delete_deadline(self, deadline_id: int) -> bool:
        deadline = self.get_deadline(deadline_id)
        if not deadline:
            return False
        self.db.delete(deadline)
        self.db.commit()
        return True

    def mark_complete(self, deadline_id: int) -> Optional[Deadline]:
        deadline = self.get_deadline(deadline_id)
        if not deadline:
            return None
        deadline.completed = True
        deadline.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(deadline)
        return deadline

    def extend_deadline(self, deadline_id: int, new_due_date: datetime) -> Optional[Deadline]:
        deadline = self.get_deadline(deadline_id)
        if not deadline:
            return None
        deadline.due_date = new_due_date
        deadline.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(deadline)
        return deadline

    def get_recurring_deadlines(self) -> List[Deadline]:
        return self.db.query(Deadline).filter(Deadline.recurrence != DeadlineRecurrence.NONE).all() 