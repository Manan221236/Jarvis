from .task import Task, TaskStatus, TaskPriority
from .user import User

__all__ = ["Task", "TaskStatus", "TaskPriority", "User"]
try:
    from .project import Project, ProjectStatus
    __all__ = ["Task", "TaskStatus", "TaskPriority", "User", "Project", "ProjectStatus"]
except ImportError:
    __all__ = ["Task", "TaskStatus", "TaskPriority", "User"]