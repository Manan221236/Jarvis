# smart_scheduler/services/project_service.py - NEW FILE
from sqlalchemy.orm import Session
from smart_scheduler.models.project import Project, ProjectStatus
from typing import List, Optional
from datetime import datetime, date

class ProjectService:
    """Service layer for project operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        deadline: datetime = None,
        start_date: Optional[date] = None,
        color: str = "#3B82F6"
    ) -> Project:
        """Create a new project"""
        
        project = Project(
            name=name,
            description=description,
            deadline=deadline,
            start_date=start_date or date.today(),
            color=color
        )
        
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        
        return project
    
    def get_projects(
        self,
        status: Optional[ProjectStatus] = None,
        include_completed: bool = True
    ) -> List[Project]:
        """Get all projects with optional filtering"""
        
        query = self.db.query(Project)
        
        if status:
            query = query.filter(Project.status == status)
        elif not include_completed:
            query = query.filter(Project.status != ProjectStatus.COMPLETED)
        
        return query.order_by(Project.deadline.asc()).all()
    
    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """Get a specific project by ID"""
        return self.db.query(Project).filter(Project.id == project_id).first()
    
    def get_upcoming_deadlines(self, days_ahead: int = 7) -> List[Project]:
        """Get projects with deadlines in the next X days"""
        
        from datetime import timedelta
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        
        return (
            self.db.query(Project)
            .filter(
                Project.deadline <= cutoff_date,
                Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNING])
            )
            .order_by(Project.deadline.asc())
            .all()
        )
    
    def update_project_progress(self, project_id: int) -> Optional[Project]:
        """Auto-calculate project progress based on completed tasks"""
        
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None
        
        # Import here to avoid circular imports
        from smart_scheduler.models.task import Task, TaskStatus
        
        # Get all tasks for this project
        project_tasks = (
            self.db.query(Task)
            .filter(Task.project_id == project_id)
            .all()
        )
        
        total_tasks = len(project_tasks)
        if total_tasks == 0:
            project.progress_percentage = 0.0
        else:
            completed_tasks = sum(1 for task in project_tasks if task.status == TaskStatus.COMPLETED)
            project.progress_percentage = (completed_tasks / total_tasks) * 100
        
        # Check if project should be marked as completed
        if project.progress_percentage == 100.0 and project.status != ProjectStatus.COMPLETED:
            project.status = ProjectStatus.COMPLETED
            project.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(project)
        
        return project