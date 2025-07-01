# smart_scheduler/models/task.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from smart_scheduler.core.database import Base
from datetime import datetime
import enum
from sqlalchemy import Enum

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # Time management
    estimated_duration = Column(Integer)  # in minutes
    actual_duration = Column(Integer)     # in minutes
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Categories and tags
    category = Column(String, index=True)
    tags = Column(String)  # JSON string for now
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    
    # TEMPORARY PROPERTIES TO FIX ERRORS - Remove when adding real subtask support
    @property
    def subtasks(self):
        """Temporary property to prevent template errors"""
        return []

    @property  
    def is_parent(self):
        """Temporary property to prevent template errors"""
        return False

    @property
    def is_subtask(self):
        """Temporary property to prevent template errors"""
        return False
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"