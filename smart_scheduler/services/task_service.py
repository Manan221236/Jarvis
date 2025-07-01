# smart_scheduler/services/task_service.py - ENHANCED VERSION
from sqlalchemy.orm import Session
from smart_scheduler.models.task import Task, TaskStatus, TaskPriority
from typing import List, Optional
from datetime import datetime

class TaskService:
    """Service layer for task operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        category: Optional[str] = None,
        estimated_duration: Optional[int] = None,
        due_date: Optional[datetime] = None,
        tags: Optional[str] = None,
        # NEW ENHANCED PARAMETERS (with defaults for backward compatibility)
        scheduled_start_time: Optional[datetime] = None,
        scheduled_end_time: Optional[datetime] = None,
        project_id: Optional[int] = None,
        energy_level_required: int = 3,
        focus_level_required: int = 3
    ) -> Task:
        """Create a new task"""
        
        task = Task(
            title=title,
            description=description,
            priority=priority,
            category=category,
            estimated_duration=estimated_duration,
            due_date=due_date,
            tags=tags,
            # NEW ENHANCED FIELDS
            scheduled_start_time=scheduled_start_time,
            scheduled_end_time=scheduled_end_time,
            project_id=project_id,
            energy_level_required=energy_level_required,
            focus_level_required=focus_level_required
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def get_tasks(
        self,
        status: Optional[TaskStatus] = None,
        category: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
        project_id: Optional[int] = None,  # NEW
        limit: int = 100
    ) -> List[Task]:
        """Get tasks with optional filtering"""
        
        query = self.db.query(Task)
        
        if status:
            query = query.filter(Task.status == status)
        
        if category:
            query = query.filter(Task.category == category)
        
        if priority:
            query = query.filter(Task.priority == priority)
            
        if project_id:  # NEW
            query = query.filter(Task.project_id == project_id)
        
        return query.order_by(Task.created_at.desc()).limit(limit).all()
    
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Get a specific task by ID"""
        return self.db.query(Task).filter(Task.id == task_id).first()
    
    def update_task_status(self, task_id: int, status: TaskStatus) -> Optional[Task]:
        """Update task status"""
        task = self.get_task_by_id(task_id)
        if not task:
            return None
        
        task.status = status
        task.updated_at = datetime.utcnow()
        
        # NEW: If completing task, set completed_at
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
            task.progress_percentage = 100.0
        
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        task = self.get_task_by_id(task_id)
        if not task:
            return False
        
        self.db.delete(task)
        self.db.commit()
        return True
    
    def get_task_stats(self) -> dict:
        """Get task statistics"""
        total = self.db.query(Task).count()
        completed = self.db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
        in_progress = self.db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
        pending = self.db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
        scheduled = self.db.query(Task).filter(Task.status == TaskStatus.SCHEDULED).count()  # NEW
        
        completion_rate = round((completed / total * 100) if total > 0 else 0, 1)
        
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "scheduled": scheduled,  # NEW
            "completion_rate": completion_rate
        }
    
    # NEW ENHANCED METHODS
    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
        category: Optional[str] = None,
        estimated_duration: Optional[int] = None,
        due_date: Optional[datetime] = None,
        tags: Optional[str] = None,
        scheduled_start_time: Optional[datetime] = None,
        scheduled_end_time: Optional[datetime] = None,
        project_id: Optional[int] = None
    ) -> Optional[Task]:
        """Update an existing task"""
        
        task = self.get_task_by_id(task_id)
        if not task:
            return None
        
        # Update only provided fields
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if priority is not None:
            task.priority = priority
        if category is not None:
            task.category = category
        if estimated_duration is not None:
            task.estimated_duration = estimated_duration
        if due_date is not None:
            task.due_date = due_date
        if tags is not None:
            task.tags = tags
        if scheduled_start_time is not None:
            task.scheduled_start_time = scheduled_start_time
        if scheduled_end_time is not None:
            task.scheduled_end_time = scheduled_end_time
        if project_id is not None:
            task.project_id = project_id
        
        task.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def get_scheduled_tasks_for_date(self, target_date: datetime.date) -> List[Task]:
        """Get all scheduled tasks for a specific date"""
        from datetime import time
        
        start_of_day = datetime.combine(target_date, time.min)
        end_of_day = datetime.combine(target_date, time.max)
        
        return (
            self.db.query(Task)
            .filter(
                Task.scheduled_start_time >= start_of_day,
                Task.scheduled_start_time <= end_of_day,
                Task.status == TaskStatus.SCHEDULED
            )
            .order_by(Task.scheduled_start_time.asc())
            .all()
        )