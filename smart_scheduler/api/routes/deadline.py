from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
from smart_scheduler.services.deadline_service import DeadlineService
from smart_scheduler.models import Deadline, DeadlineType, DeadlineRecurrence
from smart_scheduler.core.database import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/api/deadlines", tags=["Deadlines"])

class DeadlineCreate(BaseModel):
    title: str
    due_date: datetime
    description: Optional[str] = None
    type: DeadlineType = DeadlineType.GENERAL
    color: Optional[str] = None
    recurrence: DeadlineRecurrence = DeadlineRecurrence.NONE
    recurrence_end_date: Optional[datetime] = None
    task_id: Optional[int] = None
    project_id: Optional[int] = None

class DeadlineUpdate(BaseModel):
    title: Optional[str]
    due_date: Optional[datetime]
    description: Optional[str]
    type: Optional[DeadlineType]
    color: Optional[str]
    recurrence: Optional[DeadlineRecurrence]
    recurrence_end_date: Optional[datetime]
    task_id: Optional[int]
    project_id: Optional[int]

class DeadlineResponse(BaseModel):
    id: int
    title: str
    due_date: datetime
    description: Optional[str]
    type: DeadlineType
    color: Optional[str]
    recurrence: DeadlineRecurrence
    recurrence_end_date: Optional[datetime]
    completed: bool
    completed_at: Optional[datetime]
    task_id: Optional[int]
    project_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

@router.get("/", response_model=List[DeadlineResponse])
def list_deadlines(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    completed: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    service = DeadlineService(db)
    return service.get_deadlines(start_date, end_date, completed)

@router.post("/", response_model=DeadlineResponse)
def create_deadline(deadline: DeadlineCreate, db: Session = Depends(get_db)):
    service = DeadlineService(db)
    return service.create_deadline(**deadline.dict())

@router.get("/analytics", response_model=Dict[str, int])
def deadline_analytics(db: Session = Depends(get_db)):
    service = DeadlineService(db)
    now = datetime.utcnow()
    all_deadlines = service.get_deadlines_plain()
    completed = sum(1 for d in all_deadlines if d["completed"])
    overdue = sum(1 for d in all_deadlines if not d["completed"] and d["due_date"] < now)
    upcoming = sum(1 for d in all_deadlines if not d["completed"] and d["due_date"] >= now)
    by_type = {t.value: 0 for t in DeadlineType}
    for d in all_deadlines:
        by_type[d["type"]] += 1
    return {
        "total": len(all_deadlines),
        "completed": completed,
        "overdue": overdue,
        "upcoming": upcoming,
        **{f"type_{k}": v for k, v in by_type.items()}
    }

@router.get("/{deadline_id}", response_model=DeadlineResponse)
def get_deadline(deadline_id: int, db: Session = Depends(get_db)):
    service = DeadlineService(db)
    deadline = service.get_deadline(deadline_id)
    if not deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")
    return deadline

@router.put("/{deadline_id}", response_model=DeadlineResponse)
def update_deadline(deadline_id: int, update: DeadlineUpdate, db: Session = Depends(get_db)):
    service = DeadlineService(db)
    deadline = service.update_deadline(deadline_id, **update.dict(exclude_unset=True))
    if not deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")
    return deadline

@router.delete("/{deadline_id}")
def delete_deadline(deadline_id: int, db: Session = Depends(get_db)):
    service = DeadlineService(db)
    if not service.delete_deadline(deadline_id):
        raise HTTPException(status_code=404, detail="Deadline not found")
    return {"message": "Deadline deleted", "deadline_id": deadline_id}

@router.patch("/{deadline_id}/complete", response_model=DeadlineResponse)
def mark_complete(deadline_id: int, db: Session = Depends(get_db)):
    service = DeadlineService(db)
    deadline = service.mark_complete(deadline_id)
    if not deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")
    return deadline

@router.patch("/{deadline_id}/extend", response_model=DeadlineResponse)
def extend_deadline(deadline_id: int, new_due_date: datetime, db: Session = Depends(get_db)):
    service = DeadlineService(db)
    deadline = service.extend_deadline(deadline_id, new_due_date)
    if not deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")
    return deadline 