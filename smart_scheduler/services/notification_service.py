from sqlalchemy.orm import Session
from smart_scheduler.models import Notification
from datetime import datetime, timedelta
from typing import List, Optional

class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def get_notification(self, notification_id: int) -> Optional[Notification]:
        return self.db.query(Notification).filter(Notification.id == notification_id).first()

    def get_notifications(self, user_id: Optional[int] = None, sent: Optional[bool] = None, read: Optional[bool] = None, upcoming: Optional[bool] = None) -> List[Notification]:
        query = self.db.query(Notification)
        if user_id is not None:
            query = query.filter(Notification.user_id == user_id)
        if sent is not None:
            query = query.filter(Notification.sent == sent)
        if read is not None:
            query = query.filter(Notification.read == read)
        if upcoming:
            now = datetime.utcnow()
            query = query.filter(Notification.scheduled_time > now)
        return query.order_by(Notification.scheduled_time).all()

    def create_notification(self, type: str, target_id: int, message: str, scheduled_time: datetime, user_id: Optional[int] = None) -> Notification:
        notification = Notification(
            type=type,
            target_id=target_id,
            message=message,
            scheduled_time=scheduled_time,
            user_id=user_id,
            sent=False,
            read=False,
            created_at=datetime.utcnow(),
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_sent(self, notification_id: int) -> Optional[Notification]:
        notification = self.get_notification(notification_id)
        if not notification:
            return None
        notification.sent = True
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_read(self, notification_id: int) -> Optional[Notification]:
        notification = self.get_notification(notification_id)
        if not notification:
            return None
        notification.read = True
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def delete_notification(self, notification_id: int) -> bool:
        notification = self.get_notification(notification_id)
        if not notification:
            return False
        self.db.delete(notification)
        self.db.commit()
        return True 