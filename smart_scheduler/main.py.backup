from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from smart_scheduler.core.config import settings
from smart_scheduler.core.database import get_db, create_tables
from smart_scheduler.services.task_service import TaskService
from smart_scheduler.models.task import TaskPriority, TaskStatus

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

# Pydantic models for API
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    category: Optional[str] = None
    estimated_duration: Optional[int] = None

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
    
    class Config:
        from_attributes = True

# Template helper functions
def get_status_icon(status):
    icons = {
        'pending': 'fas fa-clock',
        'in_progress': 'fas fa-play',
        'completed': 'fas fa-check',
        'cancelled': 'fas fa-times'
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

# Add helper functions to templates
templates.env.globals['get_status_icon'] = get_status_icon
templates.env.globals['format_duration'] = format_duration

# API Routes
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard page"""
    
    task_service = TaskService(db)
    
    # Get recent tasks and stats
    recent_tasks = task_service.get_tasks(limit=6)
    stats = task_service.get_task_stats()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "recent_tasks": recent_tasks,
        "stats": stats,
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
    return {"status": "healthy", "service": "Jarvis AI Assistant"}

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
        estimated_duration=task_data.estimated_duration
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
        created_at=task.created_at.strftime("%Y-%m-%d %H:%M:%S")
    )

@app.get("/api/tasks", response_model=List[TaskResponse])
def get_tasks(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all tasks with optional filtering"""
    
    # Convert string filters to enums
    status_filter = None
    if status:
        try:
            status_filter = TaskStatus(status.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    priority_filter = None
    if priority:
        try:
            priority_filter = TaskPriority(priority.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {priority}")
    
    task_service = TaskService(db)
    tasks = task_service.get_tasks(
        status=status_filter,
        category=category,
        priority=priority_filter
    )
    
    return [
        TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            category=task.category,
            estimated_duration=task.estimated_duration,
            progress_percentage=task.progress_percentage,
            created_at=task.created_at.strftime("%Y-%m-%d %H:%M:%S")
        )
        for task in tasks
    ]

@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task by ID"""
    
    task_service = TaskService(db)
    task = task_service.get_task_by_id(task_id)
    
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
        created_at=task.created_at.strftime("%Y-%m-%d %H:%M:%S")
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
        estimated_duration=task_data.estimated_duration
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
        created_at=task.created_at.strftime("%Y-%m-%d %H:%M:%S")
    )

def run_server():
    """Run the FastAPI server with proper import string for reload"""
    logger.info("🚀 Starting Jarvis AI Assistant server...")
    logger.info(f"📍 Dashboard: http://{settings.host}:{settings.port}/")
    logger.info(f"📋 Tasks: http://{settings.host}:{settings.port}/tasks")
    logger.info(f"🔌 API: http://{settings.host}:{settings.port}/api/health")
    logger.info("🎉 New features: Time scheduling, conflict detection, and more!")
    
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