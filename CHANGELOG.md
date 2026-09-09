# Changelog

All notable changes to the `tasking` package are documented here.

## Unreleased

- Added `TaskManager.clear_completed()`: removes every task whose `done`
  status is `True` and returns the removed `Task` objects in insertion
  order. Returns an empty list (and mutates nothing) when no tasks are
  completed; pending tasks are left untouched with their ids intact.

- Added `TaskManager.stats()` returning a dict with `total`, `pending`,
  `completed` and `overdue` counts. `overdue` counts only *pending* tasks
  whose `due_date` is strictly before today (via `Task.is_overdue()`), so a
  completed task with a past due date is not reported as overdue.
- 15 new tests in `tests/test_manager_stats.py` covering the empty manager,
  mixed done/pending states, tasks with and without due dates, and the
  boundary where a task due today is not overdue. Existing tests unchanged.

- Added `TaskManager.tag_counts()`: returns a dict mapping each distinct
  tag across all tasks — done and pending alike — to the number of tasks
  carrying it. Tags are counted exactly as stored by `add()` (stripped,
  case preserved); tasks without tags are skipped. Returns `{}` for an
  empty manager.
- 15 new tests in `tests/test_manager_tag_counts.py` covering the empty
  manager, single tag, repeated tags across tasks, multiple distinct tags,
  tasks without tags, combined done+pending counting, and removal.
  Existing tests unchanged.

- Added `TaskManager.due_soon(hours=48)`: returns the list of pending
  (not done) tasks whose `due_date` is set and falls within the window
  from today up to and including today + `hours` hours, sorted by
  `due_date` ascending (soonest first). Overdue tasks (due date strictly
  before today) and tasks without a due date are excluded. `hours` must
  be a non-negative number; anything else raises `TypeError`/`ValueError`.
- 16 new tests in `tests/test_due_soon.py` covering the empty manager,
  tasks well inside / well beyond the window, the inclusive 48-hour
  boundary, exclusion of done tasks, tasks without a due date and overdue
  tasks, soonest-first ordering, custom `hours` windows, and argument
  validation. Existing tests unchanged.

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
