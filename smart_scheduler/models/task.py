# smart_scheduler/models/task.py - ENHANCED VERSION
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Time, Date
from sqlalchemy.orm import relationship
from smart_scheduler.core.database import Base
from datetime import datetime, time, date
import enum
from sqlalchemy import Enum

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"  # NEW
    BLOCKED = "blocked"      # NEW

class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskRecurrence(str, enum.Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # EXISTING Time management
    estimated_duration = Column(Integer)  # in minutes
    actual_duration = Column(Integer)     # in minutes
    
    # EXISTING Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    
    # EXISTING Categories and tags
    category = Column(String, index=True)
    tags = Column(String)  # JSON string for now
    
    # EXISTING Progress tracking
    progress_percentage = Column(Float, default=0.0)
    
    # NEW ENHANCED FIELDS (safe to add - they have defaults)
    scheduled_start_time = Column(DateTime, nullable=True)  # When task is scheduled to start
    scheduled_end_time = Column(DateTime, nullable=True)    # When task is scheduled to end
    
    # NEW Project association (will add foreign key later)
    project_id = Column(Integer, nullable=True)  # No foreign key yet to avoid errors
    
    # NEW Recurrence
    recurrence = Column(Enum(TaskRecurrence), default=TaskRecurrence.NONE)
    recurrence_end_date = Column(Date, nullable=True)
    
    # NEW Energy and focus requirements
    energy_level_required = Column(Integer, default=3)  # 1-5 scale
    focus_level_required = Column(Integer, default=3)   # 1-5 scale
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"

    def to_dict(self):
        return {
            "id": getattr(self, "id", None),
            "title": getattr(self, "title", None),
            "description": getattr(self, "description", None),
            "priority": self.priority.value if getattr(self, "priority", None) is not None else None,
            "category": getattr(self, "category", None),
            "estimated_duration": getattr(self, "estimated_duration", None),
            "due_date": self.due_date.isoformat() if getattr(self, "due_date", None) is not None else None,
            "status": self.status.value if getattr(self, "status", None) is not None else None,
            "progress_percentage": getattr(self, "progress_percentage", None),
            "created_at": self.created_at.isoformat() if getattr(self, "created_at", None) is not None else None,
            "actual_duration": getattr(self, "actual_duration", None),
            "completed_at": self.completed_at.isoformat() if getattr(self, "completed_at", None) is not None else None,
            "tags": getattr(self, "tags", None),
            "updated_at": self.updated_at.isoformat() if getattr(self, "updated_at", None) is not None else None,
            "scheduled_start_time": self.scheduled_start_time.isoformat() if getattr(self, "scheduled_start_time", None) is not None else None,
            "scheduled_end_time": self.scheduled_end_time.isoformat() if getattr(self, "scheduled_end_time", None) is not None else None,
            "project_id": getattr(self, "project_id", None),
            "recurrence": self.recurrence.value if getattr(self, "recurrence", None) is not None else None,
            "recurrence_end_date": self.recurrence_end_date.isoformat() if getattr(self, "recurrence_end_date", None) is not None else None,
            "energy_level_required": getattr(self, "energy_level_required", None),
            "focus_level_required": getattr(self, "focus_level_required", None)
        }