"""Tasking - a tiny in-memory task manager."""

from .manager import TaskManager, TaskNotFoundError

__all__ = ["TaskManager", "TaskNotFoundError"]
__version__ = "0.1.0"
