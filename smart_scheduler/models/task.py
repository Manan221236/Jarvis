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