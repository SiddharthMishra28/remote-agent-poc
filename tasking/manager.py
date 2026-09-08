"""TaskManager - deliberately minimal, a few rough edges."""
from dataclasses import dataclass, field
from typing import Optional


class TaskNotFoundError(Exception):
    pass


@dataclass
class Task:
    id: int
    title: str
    done: bool = False
    tags: list = field(default_factory=list)


class TaskManager:
    def __init__(self):
        self._tasks = {}
        self._next_id = 1

    def add(self, title, tags=None):
        t = Task(self._next_id, title, tags=tags or [])
        self._tasks[t.id] = t
        self._next_id += 1
        return t

    def complete(self, task_id):
        try:
            t = self._tasks[task_id]
        except KeyError:
            raise TaskNotFoundError(task_id)
        t.done = True
        return t

    def all(self):
        return list(self._tasks.values())

    def pending(self):
        return [t for t in self._tasks.values() if not t.done]
