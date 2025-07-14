from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from smart_scheduler.services.notification_service import NotificationService
from smart_scheduler.models import Notification
from smart_scheduler.core.database import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

class NotificationCreate(BaseModel):
    type: str  # 'task' or 'deadline'
    target_id: int
    message: str
    scheduled_time: datetime
    user_id: Optional[int] = None

class NotificationResponse(BaseModel):
    id: int
    type: str
    target_id: int
    message: str
    scheduled_time: datetime
    sent: bool
    read: bool
    user_id: Optional[int]
    created_at: datetime

    class Config:
        orm_mode = True

@router.get("/", response_model=List[NotificationResponse])
def list_notifications(
    user_id: Optional[int] = Query(None),
    sent: Optional[bool] = Query(None),
    read: Optional[bool] = Query(None),
    upcoming: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    service = NotificationService(db)
    return service.get_notifications(user_id, sent, read, upcoming)

@router.post("/", response_model=NotificationResponse)
def create_notification(notification: NotificationCreate, db: Session = Depends(get_db)):
    service = NotificationService(db)
    return service.create_notification(**notification.dict())

@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(notification_id: int, db: Session = Depends(get_db)):
    service = NotificationService(db)
    notification = service.get_notification(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.patch("/{notification_id}/sent", response_model=NotificationResponse)
def mark_sent(notification_id: int, db: Session = Depends(get_db)):
    service = NotificationService(db)
    notification = service.mark_sent(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(notification_id: int, db: Session = Depends(get_db)):
    service = NotificationService(db)
    notification = service.mark_read(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.delete("/{notification_id}")
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    service = NotificationService(db)
    if not service.delete_notification(notification_id):
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification deleted", "notification_id": notification_id} 