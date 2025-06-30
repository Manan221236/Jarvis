# smart_scheduler/services/task_service.py
# Enhanced TaskService with Scheduling Features

from sqlalchemy.orm import Session
from smart_scheduler.models.task import Task, TaskStatus, TaskPriority
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time, timedelta
import json

class TaskService:
    """Enhanced service layer for task operations with scheduling"""
    
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
        # NEW scheduling parameters
        scheduled_date: Optional[date] = None,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        all_day: bool = False,
        location: Optional[str] = None,
        energy_level: Optional[str] = None,
        focus_time_required: bool = False,
        project_id: Optional[int] = None
    ) -> Task:
        """Create a new task with optional scheduling"""
        
        # Determine status based on scheduling
        status = TaskStatus.PENDING
        if scheduled_date and start_time:
            status = TaskStatus.SCHEDULED
        
        task = Task(
            title=title,
            description=description,
            priority=priority,
            category=category,
            estimated_duration=estimated_duration,
            due_date=due_date,
            tags=tags,
            status=status,
            # NEW scheduling fields
            scheduled_date=scheduled_date,
            start_time=start_time,
            end_time=end_time,
            all_day=all_day,
            location=location,
            energy_level=energy_level,
            focus_time_required=focus_time_required,
            project_id=project_id
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
        scheduled_date: Optional[date] = None,
        project_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Task]:
        """Get tasks with enhanced filtering"""
        
        query = self.db.query(Task)
        
        if status:
            query = query.filter(Task.status == status)
        
        if category:
            query = query.filter(Task.category == category)
        
        if priority:
            query = query.filter(Task.priority == priority)
            
        if scheduled_date:
            query = query.filter(Task.scheduled_date == scheduled_date)
            
        if project_id:
            query = query.filter(Task.project_id == project_id)
        
        return query.order_by(Task.created_at.desc()).limit(limit).all()
    
    def get_tasks_by_date_range(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[Task]:
        """Get all tasks within a date range"""
        return self.db.query(Task).filter(
            Task.scheduled_date >= start_date,
            Task.scheduled_date <= end_date
        ).order_by(Task.scheduled_date, Task.start_time).all()
    
    def get_today_tasks(self) -> List[Task]:
        """Get all tasks scheduled for today"""
        today = date.today()
        return self.get_tasks(scheduled_date=today)
    
    def get_this_week_tasks(self) -> List[Task]:
        """Get all tasks for this week"""
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return self.get_tasks_by_date_range(start_of_week, end_of_week)
    
    def schedule_task(
        self,
        task_id: int,
        scheduled_date: date,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        all_day: bool = False
    ) -> Optional[Task]:
        """Schedule an existing task"""
        task = self.get_task_by_id(task_id)
        if task:
            task.scheduled_date = scheduled_date
            task.start_time = start_time
            task.end_time = end_time
            task.all_day = all_day
            task.status = TaskStatus.SCHEDULED
            task.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(task)
        
        return task
    
    def check_time_conflicts(
        self,
        scheduled_date: date,
        start_time: time,
        end_time: time,
        exclude_task_id: Optional[int] = None
    ) -> List[Task]:
        """Check for time conflicts with existing scheduled tasks"""
        query = self.db.query(Task).filter(
            Task.scheduled_date == scheduled_date,
            Task.start_time.isnot(None),
            Task.end_time.isnot(None),
            Task.status != TaskStatus.CANCELLED
        )
        
        if exclude_task_id:
            query = query.filter(Task.id != exclude_task_id)
        
        existing_tasks = query.all()
        conflicts = []
        
        for task in existing_tasks:
            # Check if times overlap
            if (start_time < task.end_time and end_time > task.start_time):
                conflicts.append(task)
        
        return conflicts
    
    def get_available_time_slots(
        self,
        date_obj: date,
        duration_minutes: int,
        start_hour: int = 9,
        end_hour: int = 17
    ) -> List[Dict[str, time]]:
        """Find available time slots for a given duration"""
        scheduled_tasks = self.db.query(Task).filter(
            Task.scheduled_date == date_obj,
            Task.start_time.isnot(None),
            Task.end_time.isnot(None)
        ).order_by(Task.start_time).all()
        
        available_slots = []
        current_time = time(start_hour, 0)
        end_time = time(end_hour, 0)
        
        for task in scheduled_tasks:
            # If there's a gap before this task
            if current_time < task.start_time:
                gap_minutes = (datetime.combine(date_obj, task.start_time) - 
                             datetime.combine(date_obj, current_time)).total_seconds() / 60
                
                if gap_minutes >= duration_minutes:
                    # Calculate end time for this slot
                    start_datetime = datetime.combine(date_obj, current_time)
                    end_datetime = start_datetime + timedelta(minutes=duration_minutes)
                    slot_end = end_datetime.time()
                    
                    available_slots.append({
                        'start_time': current_time,
                        'end_time': slot_end
                    })
            
            current_time = task.end_time
        
        # Check if there's time after the last task
        if current_time < end_time:
            remaining_minutes = (datetime.combine(date_obj, end_time) - 
                               datetime.combine(date_obj, current_time)).total_seconds() / 60
            
            if remaining_minutes >= duration_minutes:
                start_datetime = datetime.combine(date_obj, current_time)
                end_datetime = start_datetime + timedelta(minutes=duration_minutes)
                slot_end = end_datetime.time()
                
                available_slots.append({
                    'start_time': current_time,
                    'end_time': slot_end
                })
        
        return available_slots
    
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
        """Get enhanced task statistics"""
        total_tasks = self.db.query(Task).count()
        
        # Count by status
        pending = self.db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
        in_progress = self.db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
        completed = self.db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
        scheduled = self.db.query(Task).filter(Task.status == TaskStatus.SCHEDULED).count()
        cancelled = self.db.query(Task).filter(Task.status == TaskStatus.CANCELLED).count()
        
        # Count by priority
        high_priority = self.db.query(Task).filter(
            Task.priority.in_([TaskPriority.HIGH, TaskPriority.URGENT])
        ).count()
        
        # Today's tasks
        today = date.today()
        today_tasks = self.db.query(Task).filter(Task.scheduled_date == today).count()
        
        # Overdue tasks
        overdue = self.db.query(Task).filter(
            Task.due_date < datetime.utcnow(),
            Task.status != TaskStatus.COMPLETED,
            Task.status != TaskStatus.CANCELLED
        ).count()
        
        # Calculate completion rate
        completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "scheduled": scheduled,
            "cancelled": cancelled,
            "high_priority": high_priority,
            "today_tasks": today_tasks,
            "overdue": overdue,
            "completion_rate": round(completion_rate, 1)
        }
    
    def get_calendar_data(self, month: int, year: int) -> Dict[str, List[Task]]:
        """Get calendar data for a specific month"""
        start_date = date(year, month, 1)
        
        # Get last day of month
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        tasks = self.get_tasks_by_date_range(start_date, end_date)
        
        # Group tasks by date
        calendar_data = {}
        for task in tasks:
            if task.scheduled_date:
                date_str = task.scheduled_date.strftime('%Y-%m-%d')
                if date_str not in calendar_data:
                    calendar_data[date_str] = []
                calendar_data[date_str].append(task)
        
        return calendar_data