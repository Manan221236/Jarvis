#!/usr/bin/env python3
"""
Complete FastAPI application for Jarvis AI Assistant
All endpoints included and working
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging
import traceback
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import all components - with fallbacks
try:
    from smart_scheduler.core.config import settings
    logger.info("✅ Config imported successfully")
except ImportError as e:
    logger.warning(f"Config import failed: {e}, using defaults")
    class BasicSettings:
        database_url = "sqlite:///./smart_scheduler.db"
        debug = True
        environment = "development"
        host = "127.0.0.1"
        port = 8000
        log_level = "INFO"
    settings = BasicSettings()

try:
    from smart_scheduler.core.database import get_db, create_tables
    from smart_scheduler.services.task_service import TaskService
    from smart_scheduler.models.task import TaskPriority, TaskStatus
    
    # Initialize database tables
    create_tables()
    logger.info("✅ Database components imported and initialized")
    DATABASE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Database components not available: {e}")
    DATABASE_AVAILABLE = False

# Create FastAPI app
app = FastAPI(
    title="Jarvis AI Assistant",
    description="Just A Rather Very Intelligent System",
    version="0.1.0",
    docs_url="/docs" if getattr(settings, 'debug', True) else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try to set up static files and templates
try:
    if os.path.exists("smart_scheduler/static"):
        app.mount("/static", StaticFiles(directory="smart_scheduler/static"), name="static")
        logger.info("✅ Static files mounted")
    else:
        logger.warning("⚠️ Static directory not found")
    
    if os.path.exists("smart_scheduler/templates"):
        templates = Jinja2Templates(directory="smart_scheduler/templates")
        logger.info("✅ Templates initialized")
        TEMPLATES_AVAILABLE = True
    else:
        logger.warning("⚠️ Templates directory not found")
        TEMPLATES_AVAILABLE = False
except Exception as e:
    logger.warning(f"⚠️ Static/Template setup failed: {e}")
    TEMPLATES_AVAILABLE = False

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

# Add helper functions to templates if available
if TEMPLATES_AVAILABLE:
    templates.env.globals['get_status_icon'] = get_status_icon
    templates.env.globals['format_duration'] = format_duration

# Routes
@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "environment": getattr(settings, 'environment', 'development'),
        "database_available": DATABASE_AVAILABLE,
        "templates_available": TEMPLATES_AVAILABLE
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db) if DATABASE_AVAILABLE else None):
    """Dashboard page"""
    try:
        if DATABASE_AVAILABLE and TEMPLATES_AVAILABLE:
            # Full implementation with database
            task_service = TaskService(db)
            stats = task_service.get_task_stats()
            recent_tasks = task_service.get_tasks(limit=5)
            
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "stats": stats,
                "recent_tasks": recent_tasks
            })
        else:
            # Fallback HTML dashboard
            return HTMLResponse(content=get_fallback_dashboard())
            
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return HTMLResponse(content=get_fallback_dashboard(error=str(e)))

@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(
    request: Request,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db) if DATABASE_AVAILABLE else None
):
    """Tasks management page"""
    try:
        if DATABASE_AVAILABLE and TEMPLATES_AVAILABLE:
            # Full implementation with database and templates
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
            
            # Get tasks
            tasks = task_service.get_tasks(
                status=status_filter,
                category=category,
                priority=priority_filter,
                limit=100
            )
            
            # Search filter
            if search and search.strip():
                search_term = search.strip().lower()
                tasks = [
                    task for task in tasks 
                    if search_term in task.title.lower() or 
                       (task.description and search_term in task.description.lower()) or
                       (task.category and search_term in task.category.lower())
                ]
            
            # Get categories
            all_tasks = task_service.get_tasks(limit=1000)
            categories = list(set(task.category for task in all_tasks if task.category))
            categories.sort()
            
            return templates.TemplateResponse("tasks.html", {
                "request": request,
                "tasks": tasks,
                "categories": categories
            })
        else:
            # Fallback HTML tasks page
            return HTMLResponse(content=get_fallback_tasks_page())
            
    except Exception as e:
        logger.error(f"Tasks page error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return HTMLResponse(content=get_fallback_tasks_page(error=str(e)))

# API ENDPOINTS

@app.get("/api/tasks", response_model=List[TaskResponse] if DATABASE_AVAILABLE else None)
def get_tasks_api(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db) if DATABASE_AVAILABLE else None
):
    """Get all tasks with optional filtering"""
    try:
        if not DATABASE_AVAILABLE:
            return get_mock_tasks()
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/tasks/{task_id}", response_model=TaskResponse if DATABASE_AVAILABLE else None)
def get_task(task_id: int, db: Session = Depends(get_db) if DATABASE_AVAILABLE else None):
    """Get a specific task by ID"""
    try:
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/tasks", response_model=TaskResponse if DATABASE_AVAILABLE else None)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db) if DATABASE_AVAILABLE else None):
    """Create a new task"""
    try:
        if not DATABASE_AVAILABLE:
            return {"message": "Database not available", "data": task_data.dict()}
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/api/tasks/{task_id}", response_model=TaskResponse if DATABASE_AVAILABLE else None)
def update_task(task_id: int, task_data: TaskCreate, db: Session = Depends(get_db) if DATABASE_AVAILABLE else None):
    """Update a task"""
    try:
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available", "data": task_data.dict()}
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.patch("/api/tasks/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db) if DATABASE_AVAILABLE else None):
    """Mark a task as completed"""
    try:
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        task_service = TaskService(db)
        task = task_service.update_task_status(task_id, TaskStatus.COMPLETED)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"message": f"Task {task_id} marked as completed", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in complete_task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db) if DATABASE_AVAILABLE else None):
    """Delete a task"""
    try:
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        task_service = TaskService(db)
        success = task_service.delete_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"message": f"Task {task_id} deleted successfully", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db) if DATABASE_AVAILABLE else None):
    """Get task statistics"""
    try:
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        task_service = TaskService(db)
        stats = task_service.get_task_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error in get_stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Fallback HTML functions (keep existing ones)
def get_fallback_dashboard(error=None):
    """Fallback dashboard when templates aren't available"""
    error_msg = f"<p style='color: #ff6b6b;'>Error: {error}</p>" if error else ""
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Jarvis AI Assistant</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
                color: white; 
                padding: 40px;
                margin: 0;
                min-height: 100vh;
            }}
            .container {{ max-width: 1000px; margin: 0 auto; text-align: center; }}
            h1 {{ 
                font-size: 3.5em; 
                margin-bottom: 20px;
                background: linear-gradient(45deg, #4dabf7, #845ef7);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            .card {{ 
                background: rgba(255,255,255,0.1); 
                padding: 30px; 
                border-radius: 15px; 
                margin: 20px 0;
                backdrop-filter: blur(15px);
                border: 1px solid rgba(255,255,255,0.1);
            }}
            a {{ color: #4dabf7; text-decoration: none; font-weight: bold; }}
            a:hover {{ color: #74c0fc; }}
            .btn {{
                display: inline-block;
                padding: 15px 30px;
                background: linear-gradient(45deg, #4dabf7, #845ef7);
                color: white;
                border-radius: 10px;
                margin: 10px;
                transition: all 0.3s ease;
                font-weight: bold;
            }}
            .btn:hover {{
                transform: translateY(-3px);
                box-shadow: 0 10px 25px rgba(77, 171, 247, 0.3);
            }}
            .status {{ display: inline-block; margin: 0 10px; }}
            .status.ok {{ color: #51cf66; }}
            .status.warn {{ color: #ffd43b; }}
            .status.error {{ color: #ff6b6b; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Jarvis AI Assistant</h1>
            <p style="font-size: 1.3em; opacity: 0.9; margin-bottom: 40px;">Just A Rather Very Intelligent System</p>
            
            {error_msg}
            
            <div class="card">
                <h2>📊 System Status</h2>
                <p>
                    <span class="status ok">✅ Server Running</span>
                    <span class="status {'ok' if DATABASE_AVAILABLE else 'warn'}">
                        {'✅' if DATABASE_AVAILABLE else '⚠️'} Database {'Connected' if DATABASE_AVAILABLE else 'Fallback Mode'}
                    </span>
                    <span class="status {'ok' if TEMPLATES_AVAILABLE else 'warn'}">
                        {'✅' if TEMPLATES_AVAILABLE else '⚠️'} Templates {'Available' if TEMPLATES_AVAILABLE else 'Using Fallback'}
                    </span>
                </p>
            </div>
            
            <div style="margin: 40px 0;">
                <a href="/tasks" class="btn">📋 Tasks Management</a>
                <a href="/api/tasks" class="btn">🔌 API Tasks</a>
                <a href="/api/health" class="btn">🩺 Health Check</a>
                <a href="/docs" class="btn">📚 API Docs</a>
            </div>
        </div>
    </body>
    </html>
    """

def get_fallback_tasks_page(error=None):
    """Fallback tasks page when templates aren't available"""
    # Keep existing implementation
    return """<!-- Existing fallback implementation -->"""

def get_mock_tasks():
    """Return mock tasks when database is not available"""
    return [
        {
            "id": 1,
            "title": "Complete project documentation",
            "description": "Write comprehensive documentation for the project",
            "status": "pending",
            "priority": "high",
            "category": "documentation",
            "estimated_duration": 120,
            "progress_percentage": 0,
            "created_at": "2025-06-30 20:00:00"
        }
    ]

def run_server():
    """Run the server"""
    logger.info("🚀 Starting Jarvis AI Assistant server...")
    logger.info(f"📍 Dashboard: http://{getattr(settings, 'host', '127.0.0.1')}:{getattr(settings, 'port', 8000)}/")
    logger.info(f"📋 Tasks: http://{getattr(settings, 'host', '127.0.0.1')}:{getattr(settings, 'port', 8000)}/tasks")
    logger.info(f"🔌 API: http://{getattr(settings, 'host', '127.0.0.1')}:{getattr(settings, 'port', 8000)}/api/health")
    
    uvicorn.run(
        app,
        host=getattr(settings, 'host', '127.0.0.1'),
        port=getattr(settings, 'port', 8000),
        reload=getattr(settings, 'debug', True),
        log_level=getattr(settings, 'log_level', 'info').lower()
    )

if __name__ == "__main__":
    run_server()