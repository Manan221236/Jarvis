from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from smart_scheduler.core.database import Base
from datetime import datetime

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)  # For future multi-user support
    type = Column(String, nullable=False)  # 'task' or 'deadline'
    target_id = Column(Integer, nullable=False)  # Task or Deadline ID
    message = Column(String, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    sent = Column(Boolean, default=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, target_id={self.target_id}, scheduled_time={self.scheduled_time})>" 