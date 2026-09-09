# Changelog

All notable changes to the `tasking` package are documented here.

## Unreleased

- Added `TaskManager.complete_all()`: marks every currently-pending task
  as done in one call and returns the `Task` objects completed by this
  call, in insertion order. Already-done tasks are not included in the
  return value; on an empty or all-done manager it returns `[]`.
- 9 new tests in `tests/test_complete_all.py` covering the empty manager,
  the all-done manager, a mixed manager (only pending tasks completed and
  returned, in insertion order), `done` flags afterwards, and `stats()`
  reflecting the new state. Existing tests unchanged.

- Added `TaskManager.reschedule(task_id, due_date=None, priority=None)`:
  updates an existing task's `due_date` and/or `priority` in place and
  returns the updated `Task`. Only the fields explicitly provided are
  changed; passing `None` for a field leaves it unchanged. Raises
  `TaskNotFoundError` for unknown ids and validates inputs with the same
  rules as `add()` (bad priority raises `ValueError`/`TypeError`, bad
  `due_date` is parsed like `add()`). Updates are all-or-nothing: if any
  provided field fails validation, no field is changed.
- 17 new tests in `tests/test_reschedule.py` covering unknown ids, no-op
  calls, due-date-only, priority-only and both-at-once updates, validation
  errors (bad priority value/type, bad date string/type), atomicity on
  validation failure, isolation from other tasks, and interaction with
  `stats()`/`is_overdue()` when rescheduling a task out of and into
  overdue. Existing tests unchanged.

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
