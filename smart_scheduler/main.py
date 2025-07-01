# smart_scheduler/main.py - ENHANCED VERSION (compatible with existing)
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date
import logging

# EXISTING IMPORTS
from smart_scheduler.core.config import settings
from smart_scheduler.core.database import get_db, create_tables
from smart_scheduler.services.task_service import TaskService
from smart_scheduler.models.task import TaskPriority, TaskStatus

# NEW IMPORTS (safe - they won't break existing code)
try:
    from smart_scheduler.services.project_service import ProjectService
    from smart_scheduler.models.project import Project, ProjectStatus
    PROJECT_FEATURES_ENABLED = True
except ImportError:
    PROJECT_FEATURES_ENABLED = False
    print("Project features not available yet - continuing with basic features")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("✅ Config imported successfully")

# Initialize database tables
create_tables()
logger.info("✅ Database components imported and initialized")

app = FastAPI(
    title="Jarvis AI Assistant",
    description="Just A Rather Very Intelligent System and assistant",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="smart_scheduler/static"), name="static")
templates = Jinja2Templates(directory="smart_scheduler/templates")

logger.info("✅ Static files mounted")
logger.info("✅ Templates initialized")

# ENHANCED Pydantic models (backward compatible)
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    category: Optional[str] = None
    estimated_duration: Optional[int] = None
    # NEW OPTIONAL FIELDS (won't break existing API calls)
    due_date: Optional[datetime] = None
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    project_id: Optional[int] = None
    energy_level_required: Optional[int] = 3
    focus_level_required: Optional[int] = 3
    tags: Optional[str] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    category: Optional[str]
    estimated_duration: Optional[int]
    progress_percentage: float
    created_at: str
    # NEW OPTIONAL FIELDS (safe to add)
    actual_duration: Optional[int] = None
    scheduled_start_time: Optional[str] = None
    scheduled_end_time: Optional[str] = None
    due_date: Optional[str] = None
    project_id: Optional[int] = None
    energy_level_required: Optional[int] = 3
    focus_level_required: Optional[int] = 3
    
    class Config:
        from_attributes = True

# NEW Project models (only if enabled)
if PROJECT_FEATURES_ENABLED:
    class ProjectCreate(BaseModel):
        name: str
        description: Optional[str] = None
        deadline: datetime
        start_date: Optional[date] = None
        color: str = "#3B82F6"

    class ProjectResponse(BaseModel):
        id: int
        name: str
        description: Optional[str]
        status: str
        start_date: Optional[str]
        deadline: str
        progress_percentage: float
        color: str
        
        class Config:
            from_attributes = True

# Template helper functions (EXISTING + ENHANCED)
def get_status_icon(status):
    icons = {
        'pending': 'fas fa-clock',
        'in_progress': 'fas fa-play',
        'completed': 'fas fa-check',
        'cancelled': 'fas fa-times',
        'scheduled': 'fas fa-calendar-check',  # NEW
        'blocked': 'fas fa-ban'                # NEW
    }
    return icons.get(status, 'fas fa-clock')

def format_duration(minutes):
    if not minutes:
        return 'Not set'
    if minutes < 60:
        return f'{minutes}m'
    hours = minutes // 60
    mins = minutes % 60
    return f'{hours}h {mins}m' if mins else f'{hours}h'

def format_datetime(dt):
    """NEW helper function"""
    if not dt:
        return None
    if isinstance(dt, str):
        return dt
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# Add helper functions to templates
templates.env.globals['get_status_icon'] = get_status_icon
templates.env.globals['format_duration'] = format_duration
templates.env.globals['format_datetime'] = format_datetime

# EXISTING API Routes (enhanced but compatible)
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard page"""
    
    task_service = TaskService(db)
    
    # Get recent tasks and stats
    recent_tasks = task_service.get_tasks(limit=6)
    stats = task_service.get_task_stats()
    
    # NEW: Get projects if available
    active_projects = []
    upcoming_deadlines = []
    
    if PROJECT_FEATURES_ENABLED:
        try:
            project_service = ProjectService(db)
            active_projects = project_service.get_projects(status=ProjectStatus.ACTIVE)
            upcoming_deadlines = project_service.get_upcoming_deadlines(days_ahead=7)
        except Exception as e:
            logger.warning(f"Project features not available: {e}")
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "recent_tasks": recent_tasks,
        "stats": stats,
        "active_projects": active_projects,
        "upcoming_deadlines": upcoming_deadlines,
        "page_title": "Dashboard"
    })

@app.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request, db: Session = Depends(get_db)):
    """Tasks management page"""
    
    task_service = TaskService(db)
    tasks = task_service.get_tasks()
    
    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "tasks": tasks,
        "page_title": "Tasks"
    })

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "Jarvis AI Assistant",
        "project_features": PROJECT_FEATURES_ENABLED
    }

# ENHANCED task creation (backward compatible)
@app.post("/api/tasks", response_model=TaskResponse)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
    
    # Convert string priority to enum
    try:
        priority_enum = TaskPriority(task_data.priority.lower())
    except ValueError:
        priority_enum = TaskPriority.MEDIUM
    
    task_service = TaskService(db)
    task = task_service.create_task(
        title=task_data.title,
        description=task_data.description,
        priority=priority_enum,
        category=task_data.category,
        estimated_duration=task_data.estimated_duration,
        # NEW ENHANCED FIELDS (safe - have defaults)
        due_date=task_data.due_date,
        scheduled_start_time=task_data.scheduled_start_time,
        scheduled_end_time=task_data.scheduled_end_time,
        project_id=task_data.project_id,
        energy_level_required=task_data.energy_level_required or 3,
        focus_level_required=task_data.focus_level_required or 3,
        tags=task_data.tags
    )
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status.value,
        priority=task.priority.value,
        category=task.category,
        estimated_duration=task.estimated_duration,
        progress_percentage=task.progress_percentage,
        created_at=task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        # NEW ENHANCED FIELDS
        actual_duration=getattr(task, 'actual_duration', None),
        scheduled_start_time=format_datetime(getattr(task, 'scheduled_start_time', None)),
        scheduled_end_time=format_datetime(getattr(task, 'scheduled_end_time', None)),
        due_date=format_datetime(getattr(task, 'due_date', None)),
        project_id=getattr(task, 'project_id', None),
        energy_level_required=getattr(task, 'energy_level_required', 3),
        focus_level_required=getattr(task, 'focus_level_required', 3)
    )

@app.patch("/api/tasks/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db)):
    """Mark a task as completed"""
    
    task_service = TaskService(db)
    task = task_service.update_task_status(task_id, TaskStatus.COMPLETED)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"message": f"Task {task_id} marked as completed", "task_id": task_id}

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task"""
    
    task_service = TaskService(db)
    success = task_service.delete_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"message": f"Task {task_id} deleted successfully", "task_id": task_id}

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get task statistics"""
    
    task_service = TaskService(db)
    stats = task_service.get_task_stats()
    
    return stats

@app.put("/api/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_data: TaskCreate, db: Session = Depends(get_db)):
    """Update an existing task"""
    
    # Convert string priority to enum
    try:
        priority_enum = TaskPriority(task_data.priority.lower())
    except ValueError:
        priority_enum = TaskPriority.MEDIUM
    
    task_service = TaskService(db)
    task = task_service.update_task(
        task_id=task_id,
        title=task_data.title,
        description=task_data.description,
        priority=priority_enum,
        category=task_data.category,
        estimated_duration=task_data.estimated_duration,
        # NEW ENHANCED FIELDS
        due_date=task_data.due_date,
        scheduled_start_time=task_data.scheduled_start_time,
        scheduled_end_time=task_data.scheduled_end_time,
        project_id=task_data.project_id,
        tags=task_data.tags
    )
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status.value,
        priority=task.priority.value,
        category=task.category,
        estimated_duration=task.estimated_duration,
        progress_percentage=task.progress_percentage,
        created_at=task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        # NEW ENHANCED FIELDS
        actual_duration=getattr(task, 'actual_duration', None),
        scheduled_start_time=format_datetime(getattr(task, 'scheduled_start_time', None)),
        scheduled_end_time=format_datetime(getattr(task, 'scheduled_end_time', None)),
        due_date=format_datetime(getattr(task, 'due_date', None)),
        project_id=getattr(task, 'project_id', None),
        energy_level_required=getattr(task, 'energy_level_required', 3),
        focus_level_required=getattr(task, 'focus_level_required', 3)
    )

# NEW PROJECT API ROUTES (only if enabled)
if PROJECT_FEATURES_ENABLED:
    @app.post("/api/projects", response_model=ProjectResponse)
    def create_project(project_data: ProjectCreate, db: Session = Depends(get_db)):
        """Create a new project"""
        
        project_service = ProjectService(db)
        project = project_service.create_project(
            name=project_data.name,
            description=project_data.description,
            deadline=project_data.deadline,
            start_date=project_data.start_date,
            color=project_data.color
        )
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status.value,
            start_date=project.start_date.isoformat() if project.start_date else None,
            deadline=project.deadline.isoformat(),
            progress_percentage=project.progress_percentage,
            color=project.color
        )

    @app.get("/api/projects", response_model=List[ProjectResponse])
    def get_projects(
        status: Optional[str] = None,
        include_completed: bool = True,
        db: Session = Depends(get_db)
    ):
        """Get all projects"""
        
        project_service = ProjectService(db)
        
        status_filter = None
        if status:
            try:
                status_filter = ProjectStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        projects = project_service.get_projects(status=status_filter, include_completed=include_completed)
        
        return [
            ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                status=project.status.value,
                start_date=project.start_date.isoformat() if project.start_date else None,
                deadline=project.deadline.isoformat(),
                progress_percentage=project.progress_percentage,
                color=project.color
            )
            for project in projects
        ]

    @app.get("/api/projects/deadlines", response_model=List[ProjectResponse])
    def get_upcoming_deadlines(days_ahead: int = 7, db: Session = Depends(get_db)):
        """Get projects with upcoming deadlines"""
        
        project_service = ProjectService(db)
        projects = project_service.get_upcoming_deadlines(days_ahead=days_ahead)
        
        return [
            ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                status=project.status.value,
                start_date=project.start_date.isoformat() if project.start_date else None,
                deadline=project.deadline.isoformat(),
                progress_percentage=project.progress_percentage,
                color=project.color
            )
            for project in projects
        ]

    @app.get("/projects", response_class=HTMLResponse)
    def projects_page(request: Request, db: Session = Depends(get_db)):
        """Projects management page"""
        
        project_service = ProjectService(db)
        projects = project_service.get_projects()
        
        return templates.TemplateResponse("projects.html", {
            "request": request,
            "projects": projects,
            "page_title": "Projects"
        })

# NEW SCHEDULING API ROUTES (basic)
@app.patch("/api/tasks/{task_id}/reschedule")
def reschedule_task(
    task_id: int,
    new_start_time: datetime,
    db: Session = Depends(get_db)
):
    """Reschedule a task to a new time"""
    
    task_service = TaskService(db)
    
    # Calculate new end time based on estimated duration
    task = task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    from datetime import timedelta
    duration = task.estimated_duration or 60  # Default 1 hour
    new_end_time = new_start_time + timedelta(minutes=duration)
    
    # Update the task
    updated_task = task_service.update_task(
        task_id,
        scheduled_start_time=new_start_time,
        scheduled_end_time=new_end_time
    )
    
    if not updated_task:
        raise HTTPException(status_code=400, detail="Failed to reschedule task")
    
    # Update status to scheduled if it was pending
    if updated_task.status == TaskStatus.PENDING:
        task_service.update_task_status(task_id, TaskStatus.SCHEDULED)
    
    return {"message": "Task rescheduled successfully", "task_id": task_id}

@app.post("/api/tasks/{task_id}/start")
def start_task(task_id: int, db: Session = Depends(get_db)):
    """Start working on a task"""
    
    task_service = TaskService(db)
    task = task_service.update_task_status(task_id, TaskStatus.IN_PROGRESS)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "message": "Task started successfully",
        "task_id": task_id,
        "started_at": datetime.utcnow().isoformat()
    }

@app.post("/api/tasks/{task_id}/pause")
def pause_task(task_id: int, db: Session = Depends(get_db)):
    """Pause the current task"""
    
    task_service = TaskService(db)
    task = task_service.update_task_status(task_id, TaskStatus.PENDING)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "message": "Task paused successfully",
        "task_id": task_id
    }

def run_server():
    """Run the FastAPI server with proper import string for reload"""
    logger.info("🚀 Starting Jarvis AI Assistant server...")
    logger.info(f"📍 Dashboard: http://{settings.host}:{settings.port}/")
    logger.info(f"📋 Tasks: http://{settings.host}:{settings.port}/tasks")
    logger.info(f"🔌 API: http://{settings.host}:{settings.port}/api/health")
    if PROJECT_FEATURES_ENABLED:
        logger.info(f"📊 Projects: http://{settings.host}:{settings.port}/projects")
    logger.info("🎉 Enhanced features: Time scheduling, project management!")
    
    uvicorn.run(
        "smart_scheduler.main:app",  # Use import string for reload
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )

if __name__ == "__main__":
    run_server()