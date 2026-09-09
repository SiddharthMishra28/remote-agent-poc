# Changelog

All notable changes to this project are documented in this file.

## Unreleased

- Added `TaskManager.stats()`: returns a `dict` with keys `'total'`,
  `'pending'`, `'completed'` and `'overdue'`. `overdue` counts only
  **pending** tasks whose `due_date` is strictly in the past
  (i.e. `Task.is_overdue()`); tasks due today are not overdue, and
  completed tasks are never counted as overdue.

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
