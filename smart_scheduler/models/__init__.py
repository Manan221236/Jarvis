from .task import Task, TaskStatus, TaskPriority
from .user import User
from .deadline import Deadline, DeadlineType, DeadlineRecurrence
from .notification import Notification

__all__ = [
    "Task", "TaskStatus", "TaskPriority", "User", "Deadline", "DeadlineType", "DeadlineRecurrence"
]
try:
    from .project import Project, ProjectStatus
    __all__ = [
        "Task", "TaskStatus", "TaskPriority", "User", "Project", "ProjectStatus", "Deadline", "DeadlineType", "DeadlineRecurrence"
    ]
except ImportError:
    pass