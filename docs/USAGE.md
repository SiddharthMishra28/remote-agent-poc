# Extended usage guide

Working examples for the `tasking` package, including edge cases. Every
snippet below was executed with Python 3.12 against `tasking` v0.2.0; comments
show the actual output. Run them from the repository root.

## Contents

- [A realistic session](#a-realistic-session)
- [Titles: stripping and validation](#titles-stripping-and-validation)
- [Tags: duplicates, stripping, types](#tags-duplicates-stripping-types)
- [Due dates: accepted and rejected formats](#due-dates-accepted-and-rejected-formats)
- [Priorities](#priorities)
- [Search](#search)
- [Removing tasks and TaskNotFoundError](#removing-tasks-and-tasknotfounderror)
- [Serialization with to_dict()](#serialization-with-to_dict)
- [Edge cases worth knowing](#edge-cases-worth-knowing)

## A realistic session

```python
from datetime import date, timedelta
from tasking import TaskManager, TaskNotFoundError

m = TaskManager()

today = date.today()
bug = m.add("Fix login bug", due_date=(today - timedelta(days=3)).isoformat(),
            tags=["bug", "auth"], priority=3)
feat = m.add("Add dark mode", due_date=(today + timedelta(days=7)).isoformat(),
             tags=["feature"], priority=1)
chore = m.add("Write release notes", due_date=(today + timedelta(days=90)).isoformat(),
              tags=["docs"], priority=2)

# what is overdue right now?
[t.title for t in m.pending() if t.is_overdue()]
# ['Fix login bug']

# finish the bug, then clean up
m.complete(bug.id)
[t.title for t in m.pending()]
# ['Add dark mode', 'Write release notes']

# find and remove a task
m.search("dark")            # [Task(id=2, title='Add dark mode', ...)]
m.remove(chore.id).title    # 'Write release notes'
m.all()                     # [Task(id=1, ...), Task(id=2, ...)]
```

## Titles: stripping and validation

Titles are stripped of surrounding whitespace before storing; internal
whitespace is preserved. Empty or whitespace-only titles are rejected.

```python
from tasking import TaskManager

m = TaskManager()
m.add("  fix  the  login  bug  ").title
# 'fix  the  login  bug'

m.add("Résumé review — café ☕").title
# 'Résumé review — café ☕'

m.add("")      # ValueError: title must not be empty or whitespace-only
m.add("   ")   # ValueError: title must not be empty or whitespace-only
m.add(123)     # TypeError: title must be a string, got int
m.add(None)   # TypeError: title must be a string, got NoneType
```

## Tags: duplicates, stripping, types

Tags are stripped, must be non-empty strings, and must not repeat after
stripping. A bare string is rejected because `tags="work"` is a common
mistake. Lists, tuples and sets are all accepted; the result is always a
`list`. Tag order follows the input for lists and tuples (sets are unordered).

```python
from tasking import TaskManager

m = TaskManager()
m.add("t", tags=("a", "b")).tags   # ['a', 'b']
sorted(m.add("t", tags={"x", "y"}).tags)  # ['x', 'y']
m.add("t", tags=[]).tags          # []
m.add("t").tags                   # [] (tags defaults to a fresh list per task)

m.add("t", tags=["work", " work "])
# ValueError: duplicate tag: ' work '   <- duplicates are detected after stripping

m.add("t", tags=["Work", "work"])
# ACCEPTED: duplicate detection is exact-match after stripping, not case-insensitive

m.add("t", tags=["ok", "   "])    # ValueError: tags must not be empty or whitespace-only
m.add("t", tags="work")           # TypeError: tags must be a list of strings, not a single string
m.add("t", tags=42)               # TypeError: tags must be a list of strings, got int
m.add("t", tags=["ok", 1])        # TypeError: each tag must be a string, got int
```

## Due dates: accepted and rejected formats

`due_date` accepts an ISO-8601 `'YYYY-MM-DD'` string or a `datetime.date`
object, and stores a `datetime.date`. The string format is strict: it must be
exactly 4 digits, dash, 2 digits, dash, 2 digits, and a real calendar date.

```python
from datetime import date
from tasking import TaskManager

m = TaskManager()
m.add("t", due_date="2026-12-25").due_date   # datetime.date(2026, 12, 25)
m.add("t", due_date=date(2026, 12, 25)).due_date  # datetime.date(2026, 12, 25)
m.add("t").due_date                          # None (no due date)

# rejected strings — each raises ValueError:
#   "2026-13-01"  month 13 does not exist
#   "2026-02-30"  February 30th does not exist
#   "not-a-date"  not ISO format
#   "01-02-2026"  DD-MM-YYYY, not YYYY-MM-DD
#   "2026/01/02"  slashes, not dashes
#   "20260101"    compact form (accepted by date.fromisoformat on 3.11+, rejected here)
#   "2026-1-2"    single-digit month/day

m.add("t", due_date=20260101)  # TypeError: due_date must be an ISO-8601 date string (YYYY-MM-DD), got int
m.add("t", due_date=True)      # TypeError: due_date must be an ISO-8601 date string (YYYY-MM-DD), got bool
```

## Priorities

`priority` must be an `int` in `0-3` (default `0`). `bool` is rejected even
though it subclasses `int`.

```python
from tasking import TaskManager

m = TaskManager()
for p in range(4):
    m.add(f"p{p}", priority=p)

[t.title for t in m.by_priority(2)]  # ['p2']
m.by_priority(1)                     # [] if no task has that priority

m.add("t", priority=4)      # ValueError: priority must be in 0-3, got 4
m.add("t", priority=-1)     # ValueError: priority must be in 0-3, got -1
m.add("t", priority="1")    # TypeError: priority must be an int in 0-3, got str
m.add("t", priority=1.5)    # TypeError: priority must be an int in 0-3, got float
m.add("t", priority=True)   # TypeError: priority must be an int in 0-3, got bool
m.by_priority(9)            # ValueError: priority must be in 0-3, got 9
m.by_priority("high")       # TypeError: priority must be an int in 0-3, got str
```

## Search

Case-insensitive substring match over titles, in insertion order. An empty or
whitespace-only query matches everything.

```python
from tasking import TaskManager

m = TaskManager()
m.add("Write Docs")
m.add("write more docs")
m.add("unrelated")

[t.title for t in m.search("WRITE")]  # ['Write Docs', 'write more docs']
m.search("ration")                    # substring, not prefix-only: matches 'preparation notes'
m.search("zzz")                       # []
len(m.search(""))                     # 3 — empty query matches all tasks
len(m.search("   "))                  # 3 — whitespace query too
m.search(5)                           # TypeError: query must be a string, got int
```

## Removing tasks and TaskNotFoundError

`remove()` and `complete()` return the task they acted on. Both raise
`TaskNotFoundError` for unknown ids — including ids that were removed earlier.

```python
from tasking import TaskManager, TaskNotFoundError

m = TaskManager()
t = m.add("once")

m.remove(t.id).title   # 'once'
m.remove(t.id)         # TaskNotFoundError: Task with id 1 not found (already removed)
m.complete(999)        # TaskNotFoundError: Task with id 999 not found

try:
    m.remove(999)
except TaskNotFoundError as e:
    e.task_id   # 999 — the offending id is available on the exception
    str(e)      # 'Task with id 999 not found'
```

Ids keep increasing even after removals, so they are never reused:

```python
m = TaskManager()
a = m.add("a")
m.remove(a.id)
b = m.add("b")
b.id == a.id + 1   # True
```

## Serialization with to_dict()

`to_dict()` returns a JSON-serializable dict. The `tags` list is a copy, so
mutating the dict cannot corrupt the task.

```python
import json
from tasking import TaskManager

m = TaskManager()
t = m.add("ship it", due_date="2026-12-25", tags=["release", "q4"], priority=3)

t.to_dict()
# {'id': 1, 'title': 'ship it', 'done': False, 'tags': ['release', 'q4'],
#  'due_date': '2026-12-25', 'priority': 3}

json.dumps(t.to_dict())   # round-trips cleanly

d = t.to_dict()
d["tags"].append("junk")
t.tags   # ['release', 'q4'] — unchanged
```

## Edge cases worth knowing

These are verified behaviors that may surprise you:

```python
from datetime import date, datetime
from tasking import TaskManager, Task

# 1. is_overdue() ignores done state: a completed task with a past due date
#    still reports overdue.
m = TaskManager()
t = m.add("late", due_date="2020-01-01")
m.complete(t.id)
t.is_overdue()   # True

# 2. is_overdue() is False for tasks due today (strictly *before* today only)
#    and for tasks without a due date.
Task(id=1, title="t", due_date=date.today()).is_overdue()  # False
Task(id=1, title="t").is_overdue()                         # False

# 3. complete() is idempotent — completing twice is fine, still returns the task.
m2 = TaskManager()
t2 = m2.add("twice")
m2.complete(t2.id)
m2.complete(t2.id).done   # True

# 4. Constructing Task() directly bypasses ALL validation — only
#    TaskManager.add() validates.
Task(id=99, title="", tags=["dup", "dup"], priority=99).priority   # 99

# 5. datetime.datetime is accepted as a due_date (it subclasses date) but is
#    NOT converted; is_overdue() then raises TypeError when comparing
#    datetime to date. Pass date objects or ISO strings, not datetimes.
m3 = TaskManager()
t3 = m3.add("t", due_date=datetime(2026, 12, 25, 10, 30))
t3.due_date    # datetime.datetime(2026, 12, 25, 10, 30)
t3.is_overdue()
# TypeError: can't compare datetime.datetime to datetime.date

# 6. all() returns a copy — mutating the returned list does not affect the manager.
m4 = TaskManager()
m4.add("a")
lst = m4.all()
lst.append("junk")
len(m4.all())   # 1

# 7. Each task gets its own tags list (no shared mutable default).
x = m4.add("x")
y = m4.add("y")
x.tags.append("mutated")
y.tags   # []
```
