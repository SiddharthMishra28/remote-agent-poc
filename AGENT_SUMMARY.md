# Agent Summary

## What changed and why

The `tasking` package (`tasking/manager.py`) was a deliberately rough task
manager. It was hardened end-to-end while keeping the public API backwards
compatible (the pre-existing tests in `tests/test_manager.py` pass unchanged):

1. **Input validation on `add()`**
   - `title` must be a non-empty, non-whitespace string (`ValueError` with a
     clear message otherwise; `TypeError` for non-strings). Titles are
     stripped before storing.
   - `tags` must be an iterable of non-empty strings with no duplicates
     (`ValueError` for duplicates/empty tags, `TypeError` for non-strings or
     a bare string). Tags are stripped and stored as a list. Passing a bare
     string is rejected because it is a common mistake (`tags="work"`).
2. **`remove(task_id)`** — removes and returns the task; raises
   `TaskNotFoundError` for missing ids. `TaskNotFoundError` now carries the
   offending `task_id` and a clear message.
3. **Due dates** — `add(title, due_date=None, tags=None, priority=0)` accepts
   an ISO-8601 `YYYY-MM-DD` string (or a `datetime.date` object) and stores it
   as a `datetime.date`. Strict `YYYY-MM-DD` format is enforced with a regex
   before parsing, because Python 3.11+ `date.fromisoformat` also accepts
   compact forms like `"20260101"` which the spec disallows.
4. **`search(query)`** — case-insensitive substring search over titles.
   Empty/whitespace queries match all tasks; non-string queries raise
   `TypeError`.
5. **Priority** — `priority` must be an int in 0-3 (`ValueError`/`TypeError`
   otherwise; `bool` is explicitly rejected since it subclasses `int`).
   `by_priority(p)` filters tasks and validates its argument the same way.
6. **Richer `Task` dataclass** — new `due_date` and `priority` fields, plus
   `is_overdue()` (True iff `due_date < today`; False when no due date) and
   `to_dict()` (JSON-serializable dict; `tags` is a copy so mutating the dict
   cannot corrupt the task).
7. **Backwards compatibility** — `add(title, tags=...)` keyword style, `all()`,
   `pending()`, `complete()` and both exception import paths
   (`tasking.TaskNotFoundError` / `tasking.manager.TaskNotFoundError`) are
   unchanged. `Task` is now also exported from the package root.
8. **Tests** — `tests/test_manager_extended.py` adds 52 tests covering
   validation errors, `remove`, `search`, due dates, priorities,
   `is_overdue`, `to_dict` and edge cases (id continuity after removal,
   mutable-default isolation, JSON round-trip, full workflow). No existing
   test was modified.
9. **README.md** — added a quick-start section documenting the new API,
   a validation-rules table and how to run the tests. The example was
   executed verbatim to confirm it works.

## Files added/modified

| File | Change |
|------|--------|
| `tasking/manager.py` | Rewritten: validation helpers, `remove()`, `search()`, `by_priority()`, due dates, priority, `Task.is_overdue()`, `Task.to_dict()` |
| `tasking/__init__.py` | Export `Task`; bump `__version__` to 0.2.0 |
| `tests/test_manager_extended.py` | New — 52 extended tests (existing `tests/test_manager.py` untouched) |
| `README.md` | Quick-start usage, validation rules, test instructions |
| `AGENT_SUMMARY.md` | This file |

## How to verify

```bash
# full suite (the command named in the task)
python3 -m pytest tests/ -q

# with coverage of tasking/ (target was >90%)
python3 -m pytest tests/ -q --cov=tasking --cov-report=term-missing
```

Latest run: **54 passed**, coverage **100%** for `tasking/`
(`tasking/__init__.py` 100%, `tasking/manager.py` 100%).

Note: `pytest` was not installed in the CI environment; it was installed
alongside `pytest-cov` to run the suite (`pip install pytest pytest-cov`).

## Risks, assumptions, follow-ups

- **Assumption — strict `YYYY-MM-DD`**: the spec says ISO-8601
  `YYYY-MM-DD`, so compact forms like `"20260101"` are rejected even though
  Python 3.11+ `date.fromisoformat` accepts them. Loosen the regex in
  `_validate_due_date` if compact input should be allowed.
- **Assumption — `TypeError` vs `ValueError`**: wrong *types* raise
  `TypeError`, wrong *values* raise `ValueError`, per Python convention. The
  spec only mandated `ValueError` for empty titles and bad due-date formats,
  which is honoured.
- **Assumption — `due_date` accepts `datetime.date` objects too** (stored
  as-is); strings remain the documented interface. `datetime.datetime` is
  intentionally rejected to avoid silent time-of-day loss.
- **Behaviour change — titles/tags are now stripped** of surrounding
  whitespace before storing. Callers relying on `"  x  "` being stored verbatim
  would see a difference; this is the more useful behaviour and matches the
  "clear message" spirit of the validation requirement.
- **Behaviour change — `add()` validates eagerly**, so previously-accepted
  garbage input (empty titles, duplicate tags) now raises. This is the
  requested hardening.
- **Not serializable**: `Task` remains a plain dataclass; there is no
  `from_dict()` / persistence layer. A natural follow-up if round-tripping
  is needed.
- **`is_overdue()` ignores `done` state** — a completed task with a past due
  date still reports overdue. If "overdue" should mean "pending and past due",
  add `and not self.done` to `is_overdue()`.
- **No external dependencies added**; the package stays pure-Python as the
  repository contract requires.
