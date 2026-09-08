# Changelog

## Unreleased

- Added `TaskManager.clear_completed()`: removes every task whose `done`
  status is `True` and returns the removed `Task` objects in insertion
  order. Returns an empty list (and mutates nothing) when no tasks are
  completed; pending tasks are left untouched with their ids intact.

## v0.2.0 — hardening

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

## v0.1.0 — initial release

- `TaskManager` with `add()`, `complete()`, `pending()` and `all()`;
  `Task` dataclass with `id`, `title` and `done`.
