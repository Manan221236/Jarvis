# smart_scheduler/models/task.py
# Enhanced Task Model with Time Scheduling

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Date, Time
from sqlalchemy.orm import relationship
from smart_scheduler.core.database import Base
from datetime import datetime, date, time, timedelta
import enum
from sqlalchemy import Enum

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"  # New status for time-scheduled tasks

class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskType(str, enum.Enum):
    TASK = "task"
    PROJECT = "project"
    MILESTONE = "milestone"
    REMINDER = "reminder"

class RecurrenceType(str, enum.Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Task(Base):
    __tablename__ = "tasks"
    
    # Basic fields
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    task_type = Column(String, default="task")  # Using String instead of Enum for compatibility
    
    # Time management - ENHANCED
    estimated_duration = Column(Integer)  # in minutes
    actual_duration = Column(Integer)     # in minutes
    
    # NEW: Scheduling fields
    scheduled_date = Column(Date)         # Which day
    start_time = Column(Time)             # Start time (e.g., 09:00)
    end_time = Column(Time)               # End time (e.g., 10:30)
    all_day = Column(Boolean, default=False)  # All-day task flag
    
    # Recurrence - NEW
    recurrence_type = Column(String, default="none")
    recurrence_interval = Column(Integer, default=1)  # Every X days/weeks/months
    recurrence_end_date = Column(Date)    # When to stop recurring
    parent_task_id = Column(Integer, ForeignKey('tasks.id'))  # For recurring task instances
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = Column(DateTime)           # Hard deadline
    completed_at = Column(DateTime)
    
    # Project management - ENHANCED
    project_id = Column(Integer, ForeignKey('tasks.id'))  # Parent project
    category = Column(String, index=True)
    tags = Column(String)  # JSON string for now
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    
    # NEW: Additional fields
    location = Column(String)             # Where to do the task
    energy_level = Column(String)         # high, medium, low (for smart scheduling)
    focus_time_required = Column(Boolean, default=False)  # Needs deep focus
    
    # Notes and attachments
    notes = Column(Text)                  # Additional notes
    attachment_urls = Column(Text)        # JSON array of file URLs
    
    # Relationships
    subtasks = relationship("Task", backref="parent_task", remote_side=[id])
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    @property
    def duration_minutes(self):
        """Calculate duration from start and end time"""
        if self.start_time and self.end_time:
            start_datetime = datetime.combine(date.today(), self.start_time)
            end_datetime = datetime.combine(date.today(), self.end_time)
            
            # Handle overnight tasks
            if end_datetime < start_datetime:
                end_datetime = datetime.combine(date.today() + timedelta(days=1), self.end_time)
            
            duration = end_datetime - start_datetime
            return int(duration.total_seconds() / 60)
        return self.estimated_duration
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and self.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return datetime.utcnow() > self.due_date
        return False
    
    @property
    def is_today(self):
        """Check if task is scheduled for today"""
        if self.scheduled_date:
            return self.scheduled_date == date.today()
        return False
    
    @property
    def time_slot(self):
        """Get formatted time slot string"""
        if self.all_day:
            return "All Day"
        elif self.start_time and self.end_time:
            return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
        elif self.start_time:
            return f"From {self.start_time.strftime('%H:%M')}"
        return "No time set"