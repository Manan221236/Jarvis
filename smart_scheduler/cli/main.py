import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from typing import Optional
from datetime import datetime

from smart_scheduler.core.database import get_db, create_tables
from smart_scheduler.services.task_service import TaskService
from smart_scheduler.models.task import TaskPriority, TaskStatus

app = typer.Typer(help="🚀 Smart Study Scheduler - Your AI-powered personal assistant")
console = Console()

# Initialize database on first import
create_tables()

def get_task_service():
    """Get task service with database session"""
    db = next(get_db())
    return TaskService(db)

@app.command()
def hello():
    """👋 Welcome message and status check"""
    console.print(Panel.fit(
        "[bold blue]Smart Study Scheduler[/bold blue]\n"
        "[dim]Your AI-powered personal assistant[/dim]\n\n"
        "🚀 Ready to boost your productivity!",
        title="Welcome",
        border_style="blue"
    ))

@app.command()
def add_task(
    title: str = typer.Argument(..., help="Task title"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Task description"),
    priority: str = typer.Option("medium", "--priority", "-p", help="Priority: low, medium, high, urgent"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Task category"),
    duration: Optional[int] = typer.Option(None, "--duration", help="Estimated duration in minutes")
):
    """📝 Add a new task"""
    
    # Interactive prompts if not provided
    if not description:
        description = Prompt.ask("Enter task description (optional)", default="")
        if not description:
            description = None
    
    if not category:
        category = Prompt.ask("Enter category (optional)", default="")
        if not category:
            category = None
    
    if not duration:
        duration_input = Prompt.ask("Estimated duration in minutes (optional)", default="")
        if duration_input:
            try:
                duration = int(duration_input)
            except ValueError:
                duration = None
    
    try:
        # Convert string priority to enum
        priority_enum = TaskPriority(priority.lower())
    except ValueError:
        console.print(f"[red]Invalid priority: {priority}. Using 'medium' instead.[/red]")
        priority_enum = TaskPriority.MEDIUM
    
    # Create task in database
    task_service = get_task_service()
    task = task_service.create_task(
        title=title,
        description=description,
        priority=priority_enum,
        category=category,
        estimated_duration=duration
    )
    
    console.print(Panel(
        f"[bold green]✅ Task Created![/bold green]\n\n"
        f"[bold]ID:[/bold] {task.id}\n"
        f"[bold]Title:[/bold] {task.title}\n"
        f"[bold]Description:[/bold] {task.description or 'None'}\n"
        f"[bold]Priority:[/bold] {task.priority.value}\n"
        f"[bold]Category:[/bold] {task.category or 'None'}\n"
        f"[bold]Duration:[/bold] {task.estimated_duration or 'Not specified'} minutes",
        title="New Task",
        border_style="green"
    ))

@app.command()
def list_tasks(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    priority: Optional[str] = typer.Option(None, "--priority", "-p", help="Filter by priority")
):
    """📋 List tasks"""
    
    task_service = get_task_service()
    
    # Convert string filters to enums
    status_filter = None
    if status:
        try:
            status_filter = TaskStatus(status.lower())
        except ValueError:
            console.print(f"[red]Invalid status: {status}[/red]")
            return
    
    priority_filter = None
    if priority:
        try:
            priority_filter = TaskPriority(priority.lower())
        except ValueError:
            console.print(f"[red]Invalid priority: {priority}[/red]")
            return
    
    tasks = task_service.get_tasks(
        status=status_filter,
        category=category,
        priority=priority_filter
    )
    
    if not tasks:
        console.print("[yellow]No tasks found![/yellow]")
        return
    
    table = Table(title="📋 Your Tasks")
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Title", style="bold")
    table.add_column("Status", style="green")
    table.add_column("Priority", style="yellow")
    table.add_column("Category", style="blue")
    table.add_column("Duration", style="magenta")
    table.add_column("Created", style="dim")
    
    for task in tasks:
        table.add_row(
            str(task.id),
            task.title,
            task.status.value,
            task.priority.value,
            task.category or "-",
            f"{task.estimated_duration}m" if task.estimated_duration else "-",
            task.created_at.strftime("%m/%d %H:%M")
        )
    
    console.print(table)

@app.command()
def complete_task(task_id: int = typer.Argument(..., help="Task ID to complete")):
    """✅ Mark task as completed"""
    
    task_service = get_task_service()
    task = task_service.get_task_by_id(task_id)
    
    if not task:
        console.print(f"[red]Task #{task_id} not found![/red]")
        return
    
    if task.status == TaskStatus.COMPLETED:
        console.print(f"[yellow]Task #{task_id} is already completed![/yellow]")
        return
    
    if Confirm.ask(f"Mark task '{task.title}' as completed?"):
        updated_task = task_service.update_task_status(task_id, TaskStatus.COMPLETED)
        console.print(f"[bold green]✅ Task #{task_id} marked as completed![/bold green]")
    else:
        console.print("[yellow]Operation cancelled[/yellow]")

@app.command()
def delete_task(task_id: int = typer.Argument(..., help="Task ID to delete")):
    """🗑️ Delete a task"""
    
    task_service = get_task_service()
    task = task_service.get_task_by_id(task_id)
    
    if not task:
        console.print(f"[red]Task #{task_id} not found![/red]")
        return
    
    if Confirm.ask(f"[bold red]Delete task '{task.title}'? This cannot be undone![/bold red]"):
        success = task_service.delete_task(task_id)
        if success:
            console.print(f"[bold red]🗑️ Task #{task_id} deleted![/bold red]")
        else:
            console.print(f"[red]Failed to delete task #{task_id}[/red]")
    else:
        console.print("[yellow]Operation cancelled[/yellow]")

@app.command()
def status():
    """📊 Show current system status"""
    
    task_service = get_task_service()
    stats = task_service.get_task_stats()
    
    console.print(Panel(
        f"[bold green]✅ System Status[/bold green]\n\n"
        f"📋 Total Tasks: {stats['total']}\n"
        f"✅ Completed: {stats['completed']}\n"
        f"⏳ In Progress: {stats['in_progress']}\n"
        f"📅 Pending: {stats['pending']}\n"
        f"🎯 Completion Rate: {stats['completion_rate']}%",
        title="Status",
        border_style="green"
    ))

@app.command()
def show_task(task_id: int = typer.Argument(..., help="Task ID to show")):
    """👁️ Show detailed task information"""
    
    task_service = get_task_service()
    task = task_service.get_task_by_id(task_id)
    
    if not task:
        console.print(f"[red]Task #{task_id} not found![/red]")
        return
    
    console.print(Panel(
        f"[bold blue]📝 Task Details[/bold blue]\n\n"
        f"[bold]ID:[/bold] {task.id}\n"
        f"[bold]Title:[/bold] {task.title}\n"
        f"[bold]Description:[/bold] {task.description or 'None'}\n"
        f"[bold]Status:[/bold] {task.status.value}\n"
        f"[bold]Priority:[/bold] {task.priority.value}\n"
        f"[bold]Category:[/bold] {task.category or 'None'}\n"
        f"[bold]Duration:[/bold] {task.estimated_duration or 'Not specified'} minutes\n"
        f"[bold]Progress:[/bold] {task.progress_percentage}%\n"
        f"[bold]Created:[/bold] {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"[bold]Updated:[/bold] {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"[bold]Completed:[/bold] {task.completed_at.strftime('%Y-%m-%d %H:%M:%S') if task.completed_at else 'Not completed'}",
        title=f"Task #{task.id}",
        border_style="blue"
    ))

if __name__ == "__main__":
    app()
