from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from smart_scheduler.services.task_service import TaskService
from smart_scheduler.models.task import Task
from smart_scheduler.core.database import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

class TaskUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    priority: Optional[str]
    category: Optional[str]
    estimated_duration: Optional[int]
    due_date: Optional[datetime]
    tags: Optional[str]
    scheduled_start_time: Optional[datetime]
    scheduled_end_time: Optional[datetime]
    project_id: Optional[int]
    recurrence: Optional[str]
    completed: Optional[bool]
    status: Optional[str]

    class Config:
        orm_mode = True

@router.put("/{task_id}")
def update_task(task_id: int, update: TaskUpdate, db: Session = Depends(get_db)):
    service = TaskService(db)
    task = service.update_task(
        task_id,
        title=update.title,
        description=update.description,
        priority=update.priority,
        category=update.category,
        estimated_duration=update.estimated_duration,
        due_date=update.due_date,
        tags=update.tags,
        scheduled_start_time=update.scheduled_start_time,
        scheduled_end_time=update.scheduled_end_time,
        project_id=update.project_id
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # Optionally update status and completed fields
    if update.status:
        task.status = update.status
    if update.completed is not None:
        task.completed = update.completed
    db.commit()
    db.refresh(task)
    return task

@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    service = TaskService(db)
    task = service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task 