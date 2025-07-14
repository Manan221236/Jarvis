from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from smart_scheduler.core.database import Base
from datetime import datetime, date
import enum
from sqlalchemy import Enum

class DeadlineType(str, enum.Enum):
    GENERAL = "general"  # Standalone
    TASK = "task"        # Linked to a task
    PROJECT = "project"  # Linked to a project

class DeadlineRecurrence(str, enum.Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class Deadline(Base):
    __tablename__ = "deadlines"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text)
    type = Column(Enum(DeadlineType), default=DeadlineType.GENERAL)
    due_date = Column(DateTime, nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    color = Column(String, default="#EF4444")  # Default red, can be customized

    # Optional links
    task_id = Column(Integer, nullable=True)  # No FK for now to avoid circular import
    project_id = Column(Integer, nullable=True)

    # Recurrence
    recurrence = Column(Enum(DeadlineRecurrence), default=DeadlineRecurrence.NONE)
    recurrence_end_date = Column(Date, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Deadline(id={self.id}, title='{self.title}', due_date='{self.due_date}', completed={self.completed})>" 