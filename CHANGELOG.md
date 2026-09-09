# Changelog

All notable changes to the `tasking` package are documented here.

## Unreleased

- Added `TaskManager.stats()` returning a dict with `total`, `pending`,
  `completed` and `overdue` counts. `overdue` counts only *pending* tasks
  whose `due_date` is strictly before today (via `Task.is_overdue()`), so a
  completed task with a past due date is not reported as overdue.
- 15 new tests in `tests/test_manager_stats.py` covering the empty manager,
  mixed done/pending states, tasks with and without due dates, and the
  boundary where a task due today is not overdue. Existing tests unchanged.

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
