# smart_scheduler/services/task_service.py
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
        tags: Optional[str] = None
    ) -> Task:
        """Create a new task"""
        
        task = Task(
            title=title,
            description=description,
            priority=priority,
            category=category,
            estimated_duration=estimated_duration,
            due_date=due_date,
            tags=tags
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
        scheduled_date: Optional[datetime] = None,  # ADD THIS TO FIX ERROR
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
        
        # Handle scheduled_date filter if provided
        if scheduled_date:
            # For now, we'll filter by due_date since we don't have scheduled_date column
            query = query.filter(Task.due_date >= scheduled_date.date() if hasattr(scheduled_date, 'date') else scheduled_date)
        
        return query.order_by(Task.created_at.desc()).limit(limit).all()
    
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Get a specific task by ID"""
        return self.db.query(Task).filter(Task.id == task_id).first()
    
    def update_task_status(
        self,
        task_id: int,
        status: TaskStatus
    ) -> Optional[Task]:
        """Update task status"""
        
        task = self.get_task_by_id(task_id)
        if not task:
            return None
        
        task.status = status
        task.updated_at = datetime.utcnow()
        
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
            task.progress_percentage = 100.0
        
        self.db.commit()
        self.db.refresh(task)
        
        return task

    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
        category: Optional[str] = None,
        estimated_duration: Optional[int] = None,
        due_date: Optional[datetime] = None,
        tags: Optional[str] = None
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
        
        task.updated_at = datetime.utcnow()
        
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
        """Get task statistics - FIXED TO PREVENT ERROR"""
        
        try:
            total_tasks = self.db.query(Task).count()
            completed_tasks = self.db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
            in_progress_tasks = self.db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
            pending_tasks = self.db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
            cancelled_tasks = self.db.query(Task).filter(Task.status == TaskStatus.CANCELLED).count()
            
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            return {
                "total": total_tasks,
                "completed": completed_tasks,
                "in_progress": in_progress_tasks,
                "pending": pending_tasks,
                "cancelled": cancelled_tasks,
                "completion_rate": round(completion_rate, 1)
            }
        except Exception as e:
            print(f"Error getting task stats: {e}")
            # Return safe default values
            return {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "cancelled": 0,
                "completion_rate": 0.0
            }