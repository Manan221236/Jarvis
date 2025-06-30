from sqlalchemy.orm import Session
from smart_scheduler.models.task import Task, TaskStatus, TaskPriority
from typing import List, Optional, Dict, Any
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
        
        return query.order_by(Task.created_at.desc()).limit(limit).all()
    
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Get a specific task by ID"""
        return self.db.query(Task).filter(Task.id == task_id).first()
    
    def update_task_status(self, task_id: int, status: TaskStatus) -> Optional[Task]:
        """Update task status"""
        task = self.get_task_by_id(task_id)
        if task:
            task.status = status
            task.updated_at = datetime.utcnow()
            
            # Set completion time if marking as completed
            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.utcnow()
                task.progress_percentage = 100.0
            
            self.db.commit()
            self.db.refresh(task)
        
        return task
    
    def update_task_progress(self, task_id: int, progress: float) -> Optional[Task]:
        """Update task progress percentage"""
        task = self.get_task_by_id(task_id)
        if task:
            task.progress_percentage = max(0, min(100, progress))
            task.updated_at = datetime.utcnow()
            
            # Auto-complete if 100%
            if progress >= 100:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(task)
        
        return task
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        task = self.get_task_by_id(task_id)
        if task:
            self.db.delete(task)
            self.db.commit()
            return True
        return False
    
    def get_task_stats(self) -> Dict[str, Any]:
        """Get task statistics"""
        total_tasks = self.db.query(Task).count()
        
        # Count by status
        pending = self.db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
        in_progress = self.db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
        completed = self.db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
        cancelled = self.db.query(Task).filter(Task.status == TaskStatus.CANCELLED).count()
        
        # Count by priority
        high_priority = self.db.query(Task).filter(
            Task.priority.in_([TaskPriority.HIGH, TaskPriority.URGENT])
        ).count()
        
        # Calculate completion rate
        completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "cancelled": cancelled,
            "high_priority": high_priority,
            "completion_rate": round(completion_rate, 1)
        }
    
    def get_tasks_by_due_date(self, days_ahead: int = 7) -> List[Task]:
        """Get tasks due within specified days"""
        from datetime import timedelta
        
        end_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        return self.db.query(Task).filter(
            Task.due_date <= end_date,
            Task.status != TaskStatus.COMPLETED,
            Task.status != TaskStatus.CANCELLED
        ).order_by(Task.due_date).all()
    
    def get_overdue_tasks(self) -> List[Task]:
        """Get overdue tasks"""
        now = datetime.utcnow()
        
        return self.db.query(Task).filter(
            Task.due_date < now,
            Task.status != TaskStatus.COMPLETED,
            Task.status != TaskStatus.CANCELLED
        ).order_by(Task.due_date).all()