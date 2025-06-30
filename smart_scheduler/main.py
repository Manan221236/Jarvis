#!/usr/bin/env python3
"""
Fixed FastAPI application for Jarvis AI Assistant
Corrected imports and dependency injection
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date, time
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import components with better error handling
try:
    from smart_scheduler.core.config import settings
    logger.info("✅ Config imported successfully")
except Exception as e:
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
except Exception as e:
    logger.warning(f"Database components not available: {e}")
    DATABASE_AVAILABLE = False
    
    # Create dummy functions for when database is not available
    def get_db():
        yield None

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

# Set up static files and templates
try:
    static_dir = project_root / "smart_scheduler" / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info("✅ Static files mounted")
    else:
        logger.warning("⚠️ Static directory not found")
    
    templates_dir = project_root / "smart_scheduler" / "templates"
    if templates_dir.exists():
        templates = Jinja2Templates(directory=str(templates_dir))
        logger.info("✅ Templates initialized")
        TEMPLATES_AVAILABLE = True
    else:
        logger.warning("⚠️ Templates directory not found")
        TEMPLATES_AVAILABLE = False
except Exception as e:
    logger.warning(f"⚠️ Static/Template setup failed: {e}")
    TEMPLATES_AVAILABLE = False

# Enhanced Pydantic models
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    category: Optional[str] = None
    estimated_duration: Optional[int] = None
    # NEW scheduling fields
    scheduled_date: Optional[str] = None  # ISO date string
    start_time: Optional[str] = None      # HH:MM format
    end_time: Optional[str] = None        # HH:MM format
    all_day: bool = False
    location: Optional[str] = None
    energy_level: Optional[str] = None
    focus_time_required: bool = False
    due_date: Optional[str] = None        # ISO datetime string

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
    # NEW scheduling fields
    scheduled_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    all_day: bool = False
    location: Optional[str] = None
    energy_level: Optional[str] = None
    focus_time_required: bool = False
    due_date: Optional[str] = None
    
    class Config:
        from_attributes = True

# Template helper functions
def get_status_icon(status):
    icons = {
        'pending': 'fas fa-clock',
        'in_progress': 'fas fa-play',
        'completed': 'fas fa-check',
        'cancelled': 'fas fa-times',
        'scheduled': 'fas fa-calendar-check'
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

# Fixed dashboard route with proper dependency handling
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page"""
    try:
        if DATABASE_AVAILABLE and TEMPLATES_AVAILABLE:
            # Get database session manually
            db = next(get_db())
            if db is not None:
                task_service = TaskService(db)
                stats = task_service.get_task_stats()
                recent_tasks = task_service.get_tasks(limit=5)
                
                return templates.TemplateResponse("dashboard.html", {
                    "request": request,
                    "stats": stats,
                    "recent_tasks": recent_tasks
                })
        
        # Fallback HTML dashboard
        return HTMLResponse(content=get_fallback_dashboard())
            
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return HTMLResponse(content=get_fallback_dashboard(error=str(e)))

# Fixed tasks page route
@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(
    request: Request,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """Tasks management page"""
    try:
        if DATABASE_AVAILABLE and TEMPLATES_AVAILABLE:
            # Get database session manually
            db = next(get_db())
            if db is not None:
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
        
        # Fallback HTML tasks page
        return HTMLResponse(content=get_fallback_tasks_page())
            
    except Exception as e:
        logger.error(f"Tasks page error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return HTMLResponse(content=get_fallback_tasks_page(error=str(e)))

# API ENDPOINTS with proper dependency handling

@app.get("/api/tasks", response_model=List[TaskResponse] if DATABASE_AVAILABLE else None)
def get_tasks_api(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    scheduled_date: Optional[str] = None
):
    """Get all tasks with enhanced filtering including date"""
    try:
        if not DATABASE_AVAILABLE:
            return get_mock_tasks()
        
        # Get database session manually
        db = next(get_db())
        if db is None:
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
        
        # Parse scheduled_date filter
        scheduled_date_filter = None
        if scheduled_date:
            try:
                scheduled_date_filter = datetime.strptime(scheduled_date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid scheduled_date format. Use YYYY-MM-DD")
        
        tasks = task_service.get_tasks(
            status=status_filter,
            category=category,
            priority=priority_filter,
            scheduled_date=scheduled_date_filter
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
                created_at=task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                scheduled_date=task.scheduled_date.isoformat() if task.scheduled_date else None,
                start_time=task.start_time.strftime("%H:%M") if task.start_time else None,
                end_time=task.end_time.strftime("%H:%M") if task.end_time else None,
                all_day=task.all_day or False,
                location=task.location,
                energy_level=task.energy_level,
                focus_time_required=task.focus_time_required or False,
                due_date=task.due_date.isoformat() if task.due_date else None
            ))
        
        return task_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/tasks", response_model=TaskResponse if DATABASE_AVAILABLE else None)
def create_task_api(task_data: TaskCreate):
    """Create a new task with scheduling support"""
    try:
        if not DATABASE_AVAILABLE:
            return {"message": "Database not available", "data": task_data.dict()}
        
        # Get database session manually
        db = next(get_db())
        if db is None:
            return {"message": "Database not available", "data": task_data.dict()}
        
        try:
            priority_enum = TaskPriority(task_data.priority.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {task_data.priority}")
        
        # Parse date and time fields
        scheduled_date_obj = None
        if task_data.scheduled_date:
            try:
                scheduled_date_obj = datetime.strptime(task_data.scheduled_date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid scheduled_date format. Use YYYY-MM-DD")
        
        start_time_obj = None
        if task_data.start_time:
            try:
                start_time_obj = datetime.strptime(task_data.start_time, '%H:%M').time()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format. Use HH:MM")
        
        end_time_obj = None
        if task_data.end_time:
            try:
                end_time_obj = datetime.strptime(task_data.end_time, '%H:%M').time()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format. Use HH:MM")
        
        due_date_obj = None
        if task_data.due_date:
            try:
                due_date_obj = datetime.fromisoformat(task_data.due_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid due_date format. Use ISO format")
        
        # Check for time conflicts if scheduled
        if scheduled_date_obj and start_time_obj and end_time_obj:
            task_service = TaskService(db)
            conflicts = task_service.check_time_conflicts(
                scheduled_date_obj, start_time_obj, end_time_obj
            )
            if conflicts:
                conflict_titles = [task.title for task in conflicts]
                raise HTTPException(
                    status_code=409, 
                    detail=f"Time conflict with existing tasks: {', '.join(conflict_titles)}"
                )
        
        task_service = TaskService(db)
        task = task_service.create_task(
            title=task_data.title,
            description=task_data.description,
            priority=priority_enum,
            category=task_data.category,
            estimated_duration=task_data.estimated_duration,
            scheduled_date=scheduled_date_obj,
            start_time=start_time_obj,
            end_time=end_time_obj,
            all_day=task_data.all_day,
            location=task_data.location,
            energy_level=task_data.energy_level,
            focus_time_required=task_data.focus_time_required,
            due_date=due_date_obj
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
            scheduled_date=task.scheduled_date.isoformat() if task.scheduled_date else None,
            start_time=task.start_time.strftime("%H:%M") if task.start_time else None,
            end_time=task.end_time.strftime("%H:%M") if task.end_time else None,
            all_day=task.all_day,
            location=task.location,
            energy_level=task.energy_level,
            focus_time_required=task.focus_time_required,
            due_date=task.due_date.isoformat() if task.due_date else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Add other API endpoints following the same pattern...
@app.get("/api/tasks/{task_id}")
def get_task(task_id: int):
    """Get a specific task by ID"""
    try:
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        db = next(get_db())
        if db is None:
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
            created_at=task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            scheduled_date=task.scheduled_date.isoformat() if task.scheduled_date else None,
            start_time=task.start_time.strftime("%H:%M") if task.start_time else None,
            end_time=task.end_time.strftime("%H:%M") if task.end_time else None,
            all_day=task.all_day or False,
            location=task.location,
            energy_level=task.energy_level,
            focus_time_required=task.focus_time_required or False,
            due_date=task.due_date.isoformat() if task.due_date else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, task_data: TaskCreate):
    """Update a task"""
    try:
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available", "data": task_data.dict()}
        
        db = next(get_db())
        if db is None:
            return {"error": "Database not available"}
        
        task_service = TaskService(db)
        task = task_service.get_task_by_id(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        try:
            priority_enum = TaskPriority(task_data.priority.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {task_data.priority}")
        
        # Parse scheduling fields
        scheduled_date_obj = None
        if task_data.scheduled_date:
            try:
                scheduled_date_obj = datetime.strptime(task_data.scheduled_date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid scheduled_date format. Use YYYY-MM-DD")
        
        start_time_obj = None
        if task_data.start_time:
            try:
                start_time_obj = datetime.strptime(task_data.start_time, '%H:%M').time()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format. Use HH:MM")
        
        end_time_obj = None
        if task_data.end_time:
            try:
                end_time_obj = datetime.strptime(task_data.end_time, '%H:%M').time()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format. Use HH:MM")
        
        due_date_obj = None
        if task_data.due_date:
            try:
                due_date_obj = datetime.fromisoformat(task_data.due_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid due_date format. Use ISO format")
        
        # Update task fields
        task.title = task_data.title
        task.description = task_data.description
        task.priority = priority_enum
        task.category = task_data.category
        task.estimated_duration = task_data.estimated_duration
        task.scheduled_date = scheduled_date_obj
        task.start_time = start_time_obj
        task.end_time = end_time_obj
        task.all_day = task_data.all_day
        task.location = task_data.location
        task.energy_level = task_data.energy_level
        task.focus_time_required = task_data.focus_time_required
        task.due_date = due_date_obj
        task.updated_at = datetime.utcnow()
        
        # Update status if scheduling changed
        if scheduled_date_obj and start_time_obj and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.SCHEDULED
        
        db.commit()
        db.refresh(task)
        
        return {"message": f"Task {task_id} updated successfully", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.patch("/api/tasks/{task_id}/complete")
def complete_task(task_id: int):
    """Mark a task as completed"""
    try:
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        db = next(get_db())
        if db is None:
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
def delete_task(task_id: int):
    """Delete a task"""
    try:
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        db = next(get_db())
        if db is None:
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
def get_stats():
    """Get task statistics"""
    try:
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        db = next(get_db())
        if db is None:
            return {"error": "Database not available"}
        
        task_service = TaskService(db)
        stats = task_service.get_task_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error in get_stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Fallback functions
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📋 Tasks Management</h1>
            <p><a href="/">← Back to Dashboard</a></p>
            
            {error_msg}
            
            <div class="card">
                <h2>📊 Tasks Overview</h2>
                <p>{'Template system available but encountered an error.' if not TEMPLATES_AVAILABLE else 'Template system will be loaded here once templates are available.'}</p>
                
                <div style="margin: 20px 0;">
                    <a href="/api/tasks" class="btn">📋 View Tasks API</a>
                    <a href="/api/health" class="btn">🩺 Health Check</a>
                    <button onclick="loadTasks()" class="btn">🔄 Load Tasks</button>
                    <button onclick="createSampleTask()" class="btn">➕ Create Sample Task</button>
                </div>
                
                <div id="tasks-data" style="background: rgba(0,0,0,0.3); padding: 20px; border-radius: 8px; margin: 20px 0; max-height: 400px; overflow-y: auto;">
                    <p>Click "Load Tasks" to fetch current tasks...</p>
                </div>
            </div>
        </div>
        
        <script>
            async function loadTasks() {{
                try {{
                    const response = await fetch('/api/tasks');
                    const tasks = await response.json();
                    const container = document.getElementById('tasks-data');
                    
                    if (Array.isArray(tasks) && tasks.length > 0) {{
                        container.innerHTML = tasks.map(task => `
                            <div style="background: rgba(255,255,255,0.05); padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #4dabf7;">
                                <h4 style="color: white; margin: 0 0 5px 0;">${{task.title}}</h4>
                                <p><strong>Status:</strong> ${{task.status}} | <strong>Priority:</strong> ${{task.priority}}</p>
                                <p>${{task.description || 'No description'}}</p>
                                ${{task.scheduled_date ? `<p><strong>📅 Scheduled:</strong> ${{task.scheduled_date}} ${{task.start_time ? task.start_time + (task.end_time ? ' - ' + task.end_time : '') : ''}}</p>` : ''}}
                                ${{task.location ? `<p><strong>📍 Location:</strong> ${{task.location}}</p>` : ''}}
                                <p><small>Created: ${{task.created_at}}</small></p>
                            </div>
                        `).join('');
                    }} else {{
                        container.innerHTML = '<p>No tasks found. Create some tasks using the API!</p>';
                    }}
                }} catch (error) {{
                    document.getElementById('tasks-data').innerHTML = `<p style="color: #ff6b6b;">Error loading tasks: ${{error.message}}</p>`;
                }}
            }}
            
            async function createSampleTask() {{
                try {{
                    const today = new Date().toISOString().split('T')[0];
                    const response = await fetch('/api/tasks', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            title: `📅 Scheduled Task ${{Date.now()}}`,
                            description: 'This is a sample scheduled task with time slots',
                            priority: 'medium',
                            category: 'test',
                            estimated_duration: 60,
                            scheduled_date: today,
                            start_time: '14:00',
                            end_time: '15:00',
                            location: 'Home Office',
                            energy_level: 'medium'
                        }})
                    }});
                    
                    if (response.ok) {{
                        alert('✅ Scheduled task created successfully!');
                        loadTasks();
                    }} else {{
                        const error = await response.json();
                        alert(`❌ Failed to create task: ${{error.detail || 'Unknown error'}}`);
                    }}
                }} catch (error) {{
                    alert(`❌ Error: ${{error.message}}`);
                }}
            }}
            
            // Auto-load tasks on page load
            document.addEventListener('DOMContentLoaded', loadTasks);
        </script>
    </body>
    </html>
    """

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
            "created_at": "2025-07-01 00:00:00",
            "scheduled_date": "2025-07-01",
            "start_time": "09:00",
            "end_time": "11:00",
            "location": "Office",
            "all_day": False,
            "energy_level": "high",
            "focus_time_required": True,
            "due_date": None
        },
        {
            "id": 2,
            "title": "Review code changes",
            "description": "Review and approve pending pull requests",
            "status": "scheduled", 
            "priority": "medium",
            "category": "development",
            "estimated_duration": 60,
            "progress_percentage": 0,
            "created_at": "2025-07-01 00:00:00",
            "scheduled_date": "2025-07-01",
            "start_time": "14:00",
            "end_time": "15:00",
            "location": "Home",
            "all_day": False,
            "energy_level": "medium",
            "focus_time_required": False,
            "due_date": None
        }
    ]

def run_server():
    """Run the server"""
    logger.info("🚀 Starting Jarvis AI Assistant server...")
    logger.info(f"📍 Dashboard: http://{getattr(settings, 'host', '127.0.0.1')}:{getattr(settings, 'port', 8000)}/")
    logger.info(f"📋 Tasks: http://{getattr(settings, 'host', '127.0.0.1')}:{getattr(settings, 'port', 8000)}/tasks")
    logger.info(f"🔌 API: http://{getattr(settings, 'host', '127.0.0.1')}:{getattr(settings, 'port', 8000)}/api/health")
    logger.info(f"🎉 New features: Time scheduling, conflict detection, and more!")
    
    uvicorn.run(
        app,
        host=getattr(settings, 'host', '127.0.0.1'),
        port=getattr(settings, 'port', 8000),
        reload=getattr(settings, 'debug', True),
        log_level=getattr(settings, 'log_level', 'info').lower()
    )

if __name__ == "__main__":
    run_server()
