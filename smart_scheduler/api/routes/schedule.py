from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from smart_scheduler.services.task_service import TaskService
from smart_scheduler.services.deadline_service import DeadlineService
from smart_scheduler.models import Task, Deadline
from smart_scheduler.core.database import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/api/schedule", tags=["Schedule"])

class ScheduleItem(BaseModel):
    id: int
    type: str  # 'task' or 'deadline'
    title: str
    due_date: datetime
    color: Optional[str]
    status: Optional[str] = None  # For tasks
    completed: Optional[bool] = None
    category: Optional[str] = None
    project_id: Optional[int] = None
    recurrence: Optional[str] = None

    class Config:
        orm_mode = True

@router.get("/", response_model=List[ScheduleItem])
def get_schedule(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    type: Optional[str] = Query(None, description="task or deadline"),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None),
    completed: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    # Fetch tasks
    task_service = TaskService(db)
    tasks = task_service.get_tasks_plain(start_date, end_date)
    # Fetch deadlines
    deadline_service = DeadlineService(db)
    deadlines = deadline_service.get_deadlines_plain_range(start_date, end_date)

    items: List[ScheduleItem] = []
    if type in (None, "task"):
        for t in tasks:
            if (
                (status is None or t["status"] == status)
                and (category is None or t["category"] == category)
                and (project_id is None or t["project_id"] == project_id)
                and (completed is None or t["completed"] == completed)
            ):
                items.append(ScheduleItem(
                    id=t["id"],
                    type="task",
                    title=t["title"],
                    due_date=t["due_date"],
                    color=t["color"],
                    status=t["status"],
                    completed=t["completed"],
                    category=t["category"],
                    project_id=t["project_id"],
                    recurrence=t["recurrence"]
                ))
    if type in (None, "deadline"):
        for d in deadlines:
            if (
                (project_id is None or d["project_id"] == project_id)
                and (completed is None or d["completed"] == completed)
            ):
                items.append(ScheduleItem(
                    id=d["id"],
                    type="deadline",
                    title=d["title"],
                    due_date=d["due_date"],
                    color=d["color"],
                    completed=d["completed"],
                    project_id=d["project_id"],
                    recurrence=d["recurrence"]
                ))
    items.sort(key=lambda x: x.due_date)
    return items 