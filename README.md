# tasking

A tiny, dependency-free, in-memory task manager for Python. Tasks have a title,
optional due date, tags and a priority; the manager validates every input
eagerly and raises clear, specific exceptions.

- **No dependencies** — pure Python 3 standard library.
- **In-memory** — no persistence; each `TaskManager` instance starts empty.
- **Validated** — bad input fails fast with `TypeError` (wrong type) or
  `ValueError` (wrong value), never silent corruption.

## Installation

The package is a single module with no dependencies. Clone the repository and
import it from the repo root (there is no `pyproject.toml`/`setup.py`, so it is
not pip-installable):

```bash
git clone https://github.com/SiddharthMishra28/remote-agent-poc.git
cd remote-agent-poc
```

`import tasking` then works from the repository root, or from any directory
that has it on `sys.path`.

## Usage

```python
from datetime import date, timedelta
from tasking import TaskManager, TaskNotFoundError

m = TaskManager()

# due dates are ISO-8601 'YYYY-MM-DD' strings (or datetime.date objects)
overdue = (date.today() - timedelta(days=3)).isoformat()
soon = (date.today() + timedelta(days=7)).isoformat()
later = (date.today() + timedelta(days=90)).isoformat()

bug = m.add("Fix login bug", due_date=overdue, tags=["bug", "auth"], priority=3)
feat = m.add("Add dark mode", due_date=soon, tags=["feature"], priority=1)
chore = m.add("Write release notes", due_date=later, tags=["docs"], priority=2)

[t.title for t in m.pending() if t.is_overdue()]  # ['Fix login bug']

m.complete(bug.id)                                # mark done; returns the Task
m.search("dark")                                  # -> [Task(... 'Add dark mode' ...)]
m.by_priority(3)                                  # -> [Task(id=1, ...)]
m.remove(chore.id)                                # remove and return the Task
m.remove(chore.id)                                # raises TaskNotFoundError

m.stats()                                         # {'total': 2, 'pending': 1, 'completed': 1, 'overdue': 0}
m.stats()["overdue"]                              # 0 — completed tasks are never counted as overdue

m.add("Tag it", tags=["bug"])                     # another task with the 'bug' tag
m.tag_counts()                                    # {'bug': 2, 'auth': 1, 'feature': 1} — 'docs' went with the removed task

m.add("Deploy hotfix", due_date=(date.today() + timedelta(days=1)).isoformat())
m.due_soon()                                      # -> [Task(... 'Deploy hotfix' ...)] — pending tasks due within 48h, soonest first

m.reschedule(feat.id, due_date=later, priority=2) # update due_date and priority in place; returns the Task
m.reschedule(feat.id)                             # no-op (both fields None) — returns the task unchanged

m.complete_all()                                  # mark every pending task done; returns the completed Tasks
m.complete_all()                                  # -> [] — nothing left to complete
```

`Task` is a dataclass; `t.to_dict()` returns a JSON-serializable view:

```python
bug.to_dict()
# {'id': 1, 'title': 'Fix login bug', 'done': True, 'tags': ['bug', 'auth'],
#  'due_date': '<the overdue date from above, e.g. 2026-09-05>', 'priority': 3}
```

More examples, including edge cases, live in [docs/USAGE.md](docs/USAGE.md).

## API reference

### `TaskManager`

| Method | Signature | Description | Raises |
|--------|-----------|-------------|--------|
| `__init__` | `() -> None` | Create an empty manager; ids start at 1 and increase monotonically. | — |
| `add` | `(title, due_date=None, tags=None, priority=0) -> Task` | Validate and store a task; returns it. Title is stripped; tags are stripped, de-duplicated (after stripping) and stored as a `list`; `due_date` is stored as `datetime.date`. | `TypeError` (non-string title/tag/priority, tags as bare string, non-string non-date due_date), `ValueError` (empty title, empty/duplicate tag, bad date, priority outside 0-3) |
| `remove` | `(task_id) -> Task` | Remove and return the task with `task_id`. | `TaskNotFoundError` |
| `complete` | `(task_id) -> Task` | Mark the task done and return it. Idempotent — completing twice is fine. | `TaskNotFoundError` |
| `complete_all` | `() -> list[Task]` | Mark every pending task done in one call and return the completed tasks, in insertion order. Already-done tasks are not included; `[]` on an empty or all-done manager. | — |
| `reschedule` | `(task_id, due_date=None, priority=None) -> Task` | Update a task's `due_date` and/or `priority` in place and return it. Only provided fields change; `None` leaves a field unchanged. All-or-nothing: if any provided field fails validation, nothing changes. | `TaskNotFoundError`, `TypeError`/`ValueError` (same rules as `add()`) |
| `search` | `(query) -> list[Task]` | Case-insensitive substring search over titles, in insertion order. Empty/whitespace query matches all tasks. | `TypeError` (non-string query) |
| `by_priority` | `(p) -> list[Task]` | All tasks at priority `p`, in insertion order. | `TypeError` (non-int), `ValueError` (outside 0-3) |
| `all` | `() -> list[Task]` | Every task, in insertion order. Returns a copy. | — |
| `pending` | `() -> list[Task]` | Tasks where `done is False`. | — |
| `stats` | `() -> dict` | Counts: `total`, `pending`, `completed`, and `overdue` (pending tasks whose `due_date` is strictly before today, via `is_overdue()`). Completed tasks are never counted as overdue. | — |
| `tag_counts` | `() -> dict` | Each distinct tag across all tasks (done and pending) mapped to the number of tasks carrying it. Tasks without tags are skipped; `{}` when there are no tags. | — |
| `due_soon` | `(hours=48) -> list` | Pending tasks whose `due_date` falls within the next `hours` hours (inclusive), sorted soonest first. Overdue tasks and tasks without a due date are excluded. | `TypeError` if `hours` is not a number, `ValueError` if negative |

### `Task` (dataclass)

| Method | Signature | Description | Raises |
|--------|-----------|-------------|--------|
| `is_overdue` | `() -> bool` | `True` iff `due_date` is strictly before today. `False` when there is no due date or it is due today. Ignores `done` state. | — |
| `to_dict` | `() -> dict` | JSON-serializable view: `id`, `title`, `done`, `tags` (copy), `due_date` (ISO string or `None`), `priority`. | — |

Fields: `id: int`, `title: str`, `done: bool = False`, `tags: list = []`,
`due_date: Optional[date] = None`, `priority: int = 0`. Constructing `Task`
directly bypasses all validation (only `TaskManager.add` validates).

### Exceptions

`TaskNotFoundError(Exception)` — carries `.task_id` and a message like
`Task with id 999 not found`. Importable from both `tasking` and
`tasking.manager`.

## Error handling

Wrong **types** raise `TypeError`; wrong **values** raise `ValueError`;
unknown ids raise `TaskNotFoundError`:

```python
from tasking import TaskManager, TaskNotFoundError

m = TaskManager()
m.add("")                          # ValueError: title must not be empty or whitespace-only
m.add("t", priority=4)            # ValueError: priority must be in 0-3, got 4
m.add("t", due_date="2026-02-30") # ValueError: due_date '2026-02-30' is not a valid ISO-8601 date (YYYY-MM-DD)
m.add("t", tags=["work", "work"])  # ValueError: duplicate tag: 'work'
m.add(123)                         # TypeError: title must be a string, got int
m.add("t", tags="work")           # TypeError: tags must be a list of strings, not a single string
m.add("t", priority="1")          # TypeError: priority must be an int in 0-3, got str
m.remove(999)                      # TaskNotFoundError: Task with id 999 not found
```

Handle unknown ids explicitly:

```python
try:
    m.remove(999)
except TaskNotFoundError as e:
    print(e)          # Task with id 999 not found
    print(e.task_id)  # 999
```

## Development & testing

```bash
python3 -m pytest tests/ -q
```

135 tests (2 backwards-compatibility tests in `tests/test_manager.py`, 52
extended tests in `tests/test_manager_extended.py`, 9 `clear_completed()`
tests in `tests/test_clear_completed.py`, 15 `stats()` tests in
`tests/test_manager_stats.py`, 15 `tag_counts()` tests in
`tests/test_manager_tag_counts.py`, 16 `due_soon()` tests in
`tests/test_due_soon.py`, 17 `reschedule()` tests in
`tests/test_reschedule.py`, 9 `complete_all()` tests in
`tests/test_complete_all.py`). Requires `pytest`
(`pip install pytest`); the package itself needs only the standard library.

## Changelog

### v0.2.0 — hardening

- Input validation on `add()` for title, tags, due_date and priority; titles
  and tags are stripped before storing.
- `remove(task_id)` with `TaskNotFoundError` for unknown ids; the exception
  carries `.task_id`.
- ISO-8601 `YYYY-MM-DD` due dates (strict format — compact forms like
  `"20260101"` are rejected) stored as `datetime.date`; `Task.is_overdue()`.
- Case-insensitive `search()` over titles; `by_priority()` filtering with the
  same validation as `add()`.
- `Task` gained `due_date`, `priority` and `to_dict()`; exported from the
  package root; `__version__` bumped to `0.2.0`.
- 52 new tests in `tests/test_manager_extended.py`; existing tests unchanged.
