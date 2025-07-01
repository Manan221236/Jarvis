# smart_scheduler/models/project.py - NEW FILE
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, Date
from sqlalchemy.orm import relationship
from smart_scheduler.core.database import Base
from datetime import datetime, date
import enum
from sqlalchemy import Enum

class ProjectStatus(str, enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PLANNING)
    
    # Project timeline
    start_date = Column(Date)
    deadline = Column(DateTime, nullable=False)  # Hard deadline
    estimated_completion = Column(DateTime)      # AI predicted completion
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Color coding for calendar
    color = Column(String, default="#3B82F6")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', deadline='{self.deadline}')>"