"""TaskManager - a small in-memory task manager.

Features:
- Input validation on ``add()`` (title, tags, due_date, priority)
- ``remove()`` with ``TaskNotFoundError`` for missing ids
- ISO-8601 (YYYY-MM-DD) due dates with overdue detection
- Case-insensitive ``search()`` over titles
- Priority levels 0-3 with ``by_priority()`` filtering
"""

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class TaskNotFoundError(Exception):
    """Raised when an operation references a task id that does not exist."""

    def __init__(self, task_id):
        self.task_id = task_id
        super().__init__(f"Task with id {task_id!r} not found")


def _validate_title(title):
    if not isinstance(title, str):
        raise TypeError(f"title must be a string, got {type(title).__name__}")
    if not title.strip():
        raise ValueError("title must not be empty or whitespace-only")
    return title.strip()


def _validate_tags(tags):
    if tags is None:
        return []
    if isinstance(tags, str):
        raise TypeError("tags must be a list of strings, not a single string")
    if not isinstance(tags, (list, tuple, set)):
        raise TypeError(f"tags must be a list of strings, got {type(tags).__name__}")
    seen = set()
    result = []
    for tag in tags:
        if not isinstance(tag, str):
            raise TypeError(f"each tag must be a string, got {type(tag).__name__}")
        if not tag.strip():
            raise ValueError("tags must not be empty or whitespace-only")
        key = tag.strip()
        if key in seen:
            raise ValueError(f"duplicate tag: {tag!r}")
        seen.add(key)
        result.append(key)
    return result


def _validate_due_date(due_date):
    if due_date is None:
        return None
    if isinstance(due_date, bool):
        raise TypeError(
            "due_date must be an ISO-8601 date string (YYYY-MM-DD), got bool"
        )
    if isinstance(due_date, date):
        return due_date
    if not isinstance(due_date, str):
        raise TypeError(
            "due_date must be an ISO-8601 date string (YYYY-MM-DD), "
            f"got {type(due_date).__name__}"
        )
    if not _ISO_DATE_RE.match(due_date):
        raise ValueError(
            f"due_date {due_date!r} is not a valid ISO-8601 date (YYYY-MM-DD)"
        )
    try:
        return date.fromisoformat(due_date)
    except ValueError:
        raise ValueError(
            f"due_date {due_date!r} is not a valid ISO-8601 date (YYYY-MM-DD)"
        ) from None


def _validate_priority(priority):
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise TypeError(
            f"priority must be an int in 0-3, got {type(priority).__name__}"
        )
    if not 0 <= priority <= 3:
        raise ValueError(f"priority must be in 0-3, got {priority}")
    return priority


@dataclass
class Task:
    id: int
    title: str
    done: bool = False
    tags: list = field(default_factory=list)
    due_date: Optional[date] = None
    priority: int = 0

    def is_overdue(self) -> bool:
        """True if the task has a due date strictly before today."""
        if self.due_date is None:
            return False
        return self.due_date < date.today()

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict view of this task."""
        return {
            "id": self.id,
            "title": self.title,
            "done": self.done,
            "tags": list(self.tags),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "priority": self.priority,
        }


class TaskManager:
    def __init__(self):
        self._tasks = {}
        self._next_id = 1

    def add(self, title, due_date=None, tags=None, priority=0):
        """Add a task and return it.

        - title: non-empty string (stripped before storing)
        - due_date: ISO-8601 string 'YYYY-MM-DD' or datetime.date; optional
        - tags: iterable of non-empty strings without duplicates; optional
        - priority: int 0-3 (default 0)
        """
        title = _validate_title(title)
        tags = _validate_tags(tags)
        due = _validate_due_date(due_date)
        priority = _validate_priority(priority)
        t = Task(self._next_id, title, tags=tags, due_date=due, priority=priority)
        self._tasks[t.id] = t
        self._next_id += 1
        return t

    def remove(self, task_id):
        """Remove and return the task with the given id.

        Raises TaskNotFoundError if the id is unknown.
        """
        try:
            return self._tasks.pop(task_id)
        except KeyError:
            raise TaskNotFoundError(task_id) from None

    def complete(self, task_id):
        try:
            t = self._tasks[task_id]
        except KeyError:
            raise TaskNotFoundError(task_id) from None
        t.done = True
        return t

    def search(self, query):
        """Case-insensitive substring search over task titles.

        Returns tasks whose title contains ``query`` (case-insensitively).
        An empty/whitespace query matches all tasks.
        """
        if not isinstance(query, str):
            raise TypeError(f"query must be a string, got {type(query).__name__}")
        q = query.strip().lower()
        return [t for t in self._tasks.values() if q in t.title.lower()]

    def by_priority(self, p):
        """Return all tasks with the given priority level."""
        p = _validate_priority(p)
        return [t for t in self._tasks.values() if t.priority == p]

    def clear_completed(self) -> list:
        """Remove and return every completed task, in insertion order.

        Pending tasks are untouched; returns [] (and mutates nothing)
        when no task is completed.
        """
        removed = [t for t in self._tasks.values() if t.done]
        for t in removed:
            del self._tasks[t.id]
        return removed


    def all(self):
        return list(self._tasks.values())

    def pending(self):
        return [t for t in self._tasks.values() if not t.done]

    def stats(self) -> dict:
        """Return counts of tasks: total, pending, completed and overdue."""
        pending = [t for t in self._tasks.values() if not t.done]
        return {
            "total": len(self._tasks),
            "pending": len(pending),
            "completed": len(self._tasks) - len(pending),
            "overdue": sum(1 for t in pending if t.is_overdue()),
        }

    def tag_counts(self) -> dict:
        """Map each distinct tag across all tasks (done and pending) to the number of tasks carrying it."""
        counts: dict = {}
        for t in self._tasks.values():
            for tag in t.tags:
                counts[tag] = counts.get(tag, 0) + 1
        return counts

    def due_soon(self, hours: int = 48) -> list:
        """Return pending tasks whose due_date falls within the next ``hours`` hours, soonest first."""
        if isinstance(hours, bool) or not isinstance(hours, (int, float)):
            raise TypeError(f"hours must be a number, got {type(hours).__name__}")
        if hours < 0:
            raise ValueError(f"hours must be non-negative, got {hours}")
        now = date.today()
        deadline = now + timedelta(hours=hours)
        tasks = [
            t
            for t in self._tasks.values()
            if not t.done and t.due_date is not None and now <= t.due_date <= deadline
        ]
        return sorted(tasks, key=lambda t: t.due_date)
