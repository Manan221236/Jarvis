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

from smart_scheduler.core.config import settings
from smart_scheduler.core.database import get_db, create_tables
from smart_scheduler.services.task_service import TaskService
from smart_scheduler.models.task import TaskPriority, TaskStatus
# Initialize database tables
create_tables()

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

# HTML Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard page"""
    task_service = TaskService(db)
    stats = task_service.get_task_stats()
    recent_tasks = task_service.get_tasks(limit=5)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_tasks": recent_tasks
    })

@app.get("/tasks", response_class=HTMLResponse)
@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(
    request: Request,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Tasks management page"""
    task_service = TaskService(db)
    
    # Convert string filters to enums
    status_filter = None
    if status:
        try:
            status_filter = TaskStatus(status.lower())
        except ValueError:
            pass
    
    priority_filter = None
    if priority:
        try:
            priority_filter = TaskPriority(priority.lower())
        except ValueError:
            pass
    
    # Get tasks (basic filtering - can be enhanced with search later)
    tasks = task_service.get_tasks(
        status=status_filter,
        category=category,
        priority=priority_filter,
        limit=100
    )
    
    # Simple search filter (if search term provided)
    if search and search.strip():
        search_term = search.strip().lower()
        tasks = [
            task for task in tasks 
            if search_term in task.title.lower() or 
               (task.description and search_term in task.description.lower()) or
               (task.category and search_term in task.category.lower())
        ]
    
    # Get unique categories for filter dropdown
    all_tasks = task_service.get_tasks(limit=1000)
    categories = list(set(task.category for task in all_tasks if task.category))
    categories.sort()
    
    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "tasks": tasks,
        "categories": categories
    })
@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "environment": settings.environment}

@app.get("/api/tasks", response_model=List[TaskResponse])
def get_tasks(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all tasks with optional filtering"""
    
    task_service = TaskService(db)
    
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
    
    tasks = task_service.get_tasks(
        status=status_filter,
        category=category,
        priority=priority_filter
    )
    
    # Convert tasks to response format
    task_responses = []
    for task in tasks:
        task_responses.append(TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            category=task.category,
            estimated_duration=task.estimated_duration,
            progress_percentage=task.progress_percentage,
            created_at=task.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ))
    
    return task_responses

@app.post("/api/tasks", response_model=TaskResponse)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
    
    try:
        priority_enum = TaskPriority(task_data.priority.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid priority: {task_data.priority}")
    
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

def run_server():
    """Run the FastAPI server"""
    uvicorn.run(
        "smart_scheduler.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

if __name__ == "__main__":
    run_server()

@app.put("/api/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_data: TaskCreate, db: Session = Depends(get_db)):
    """Update a task"""
    
    task_service = TaskService(db)
    task = task_service.get_task_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        priority_enum = TaskPriority(task_data.priority.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid priority: {task_data.priority}")
    
    # Update task fields
    task.title = task_data.title
    task.description = task_data.description
    task.priority = priority_enum
    task.category = task_data.category
    task.estimated_duration = task_data.estimated_duration
    task.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    
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

@app.put("/api/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_data: TaskCreate, db: Session = Depends(get_db)):
    """Update a task"""
    
    task_service = TaskService(db)
    task = task_service.get_task_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        priority_enum = TaskPriority(task_data.priority.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid priority: {task_data.priority}")
    
    # Update task fields
    task.title = task_data.title
    task.description = task_data.description
    task.priority = priority_enum
    task.category = task_data.category
    task.estimated_duration = task_data.estimated_duration
    task.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    
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
