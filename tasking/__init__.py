"""Tasking - a tiny in-memory task manager."""

from .manager import Task, TaskManager, TaskNotFoundError

__all__ = ["TaskManager", "Task", "TaskNotFoundError"]
__version__ = "0.2.0"
