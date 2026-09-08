# remote-agent-poc

POC target for autonomous coding agent (cicd-hub unified layer)

## Quick start

```python
from tasking import TaskManager, TaskNotFoundError

m = TaskManager()

# add tasks with optional due dates (ISO-8601 YYYY-MM-DD), tags and priority (0-3)
bug = m.add("Fix login bug", due_date="2026-12-24", tags=["bug", "auth"], priority=3)
feat = m.add("Add dark mode", due_date="2030-01-01", tags=["feat"], priority=1)

m.complete(bug.id)          # mark done
m.remove(bug.id)            # delete; raises TaskNotFoundError if the id is unknown

m.search("dark")            # case-insensitive substring search over titles
m.by_priority(3)            # all tasks at priority 3
m.pending()                 # tasks that are not done yet
m.all()                     # everything

bug.is_overdue()            # True if due_date < today (False when no due date)
bug.to_dict()               # JSON-serializable view:
                           # {'id': 1, 'title': 'Fix login bug', 'done': True,
                           #  'tags': ['bug', 'auth'], 'due_date': '2026-12-24',
                           #  'priority': 3}
```

## Validation rules

| Input | Rule | Error |
|-------|------|-------|
| `title` | non-empty string (surrounding whitespace is stripped) | `ValueError` / `TypeError` |
| `tags` | iterable of non-empty strings, no duplicates | `ValueError` / `TypeError` |
| `due_date` | `'YYYY-MM-DD'` string or `datetime.date` | `ValueError` / `TypeError` |
| `priority` | integer `0-3` | `ValueError` / `TypeError` |

Missing ids raise `TaskNotFoundError` from `remove()` and `complete()`.

## Running the tests

```bash
python3 -m pytest tests/ -q
```
