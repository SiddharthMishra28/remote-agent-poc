# Agent Summary

## What changed and why

This pass added a **`stats()` method** to `TaskManager` in
`tasking/manager.py`, per the task requirements. The manager already had
`add`/`remove`/`complete`/`search`/`by_priority`/`all`/`pending` and due-date
overdue detection; `stats()` was the only new behaviour introduced.

1. **`tasking/manager.py`** — added `stats() -> dict`:
   - Returns `{'total', 'pending', 'completed', 'overdue'}`.
   - `total` = all tasks; `pending` = `done is False`; `completed` = done;
     `overdue` = **pending** tasks whose `due_date` is strictly before today
     (delegates to `Task.is_overdue()`).
   - Design decision: a *completed* task with a past due date is **not**
     counted as overdue (the task spec says "overdue = pending tasks whose
     due_date is in the past"), even though `is_overdue()` itself ignores
     `done` state. This is covered by an explicit test
     (`test_stats_completed_past_due_task_is_not_overdue`).
   - Style follows the existing API: typed return annotation, one-line
     docstring, pure stdlib, no external deps.
2. **`tests/test_manager_stats.py`** — new focused test file (15 tests):
   empty manager (all zeros), exact key set, mixed done/pending states,
   all-completed, `total == pending + completed` invariant, removal,
   with/without due dates, completed-past-due not overdue, multiple overdue
   (string and `date` object inputs), the **due-today boundary** (string and
   `date` object, plus a today/yesterday mix), and consistency with
   `all()`/`pending()`/`is_overdue()`.
3. **`CHANGELOG.md`** — created (it did not exist) with an **Unreleased**
   section describing `stats()` and the new tests, followed by the prior
   v0.2.0 hardening history (carried over from the README changelog section
   so the history lives in one place).
4. **`README.md`** — added the required 2-line `stats()` example to the usage
   section (verified by execution — see below), a `stats()` row in the
   `TaskManager` API reference table, and updated the test count (54 → 69).

## Files added/modified

| File | Change |
|------|--------|
| `tasking/manager.py` | Added `stats()` method (8 lines) |
| `tests/test_manager_stats.py` | New: 15 focused `stats()` tests |
| `CHANGELOG.md` | New: Unreleased entry for `stats()` + v0.2.0 history |
| `README.md` | 2-line `stats()` usage example, API table row, test count |
| `AGENT_SUMMARY.md` | This file (replaces the previous documentation-pass summary) |

Not modified: `tasking/__init__.py` (no new exports needed — `stats()` is a
method on `TaskManager`), `tests/test_manager.py`,
`tests/test_manager_extended.py`, `docs/USAGE.md`.

## How to verify

```bash
# 1. run the full suite (pytest must be installed: pip install pytest)
python3 -m pytest tests/ -q
# expected: 69 passed

# 2. run only the new stats tests
python3 -m pytest tests/test_manager_stats.py -q
# expected: 15 passed

# 3. spot-check stats() semantics directly
python3 -c "
from datetime import date, timedelta
from tasking import TaskManager
m = TaskManager()
m.add('late', due_date=(date.today()-timedelta(days=1)).isoformat())
m.add('today', due_date=date.today())
done = m.add('done late', due_date=(date.today()-timedelta(days=1)).isoformat())
m.complete(done.id)
print(m.stats())
# {'total': 3, 'pending': 2, 'completed': 1, 'overdue': 1}
"

# 4. verify the README usage example output (as written in README.md)
python3 -c "
from datetime import date, timedelta
from tasking import TaskManager
m = TaskManager()
bug = m.add('Fix login bug', due_date=(date.today()-timedelta(days=3)).isoformat(), tags=['bug','auth'], priority=3)
feat = m.add('Add dark mode', due_date=(date.today()+timedelta(days=7)).isoformat(), tags=['feature'], priority=1)
chore = m.add('Write release notes', due_date=(date.today()+timedelta(days=90)).isoformat(), tags=['docs'], priority=2)
m.complete(bug.id); m.remove(chore.id)
assert m.stats() == {'total': 2, 'pending': 1, 'completed': 1, 'overdue': 0}
print('README example OK')
"
```

Latest run: **69 passed** (`python3 -m pytest tests/ -q`, Python 3.12,
pytest 9.1.1) — 54 pre-existing tests unchanged and green, plus 15 new
`stats()` tests. The README example output comment was verified by executing
the snippet (an initial draft comment was wrong and corrected after this
verification caught it).

## Risks, assumptions, follow-ups

- **Assumption — overdue counts only pending tasks**: the task text says
  "overdue = pending tasks whose due_date is in the past", so completed
  tasks with past due dates are excluded from `overdue` even though
  `Task.is_overdue()` alone would report them overdue. Documented in the
  README table row and CHANGELOG, and pinned by test.
- **Assumption — CHANGELOG.md did not exist**, so it was created with an
  `Unreleased` section at the top (per the task) and the v0.2.0 history
  below it, matching the format already used in the README's changelog
  section.
- **Assumption — README length**: the previous agent's summary mentioned a
  self-imposed 150-line README target; the repo contract only requires a
  working quick-start example, so the README is now 152 lines to fit the
  API table row and example. Trimming is cosmetic if that target matters.
- **Risk — midnight boundary**: `stats()` (like `is_overdue()`) compares
  against `date.today()` at call time, so a task due today flips to overdue
  at midnight. Inherent to the existing date-based design; no timezones
  involved.
- **Risk — datetime due dates**: the pre-existing quirk where a
  `datetime.datetime` due date makes `is_overdue()` raise `TypeError` also
  affects `stats()`'s `overdue` count. Out of scope here (documented in
  `docs/USAGE.md`); follow-up would be normalizing datetimes in
  `_validate_due_date`.
- **pytest not preinstalled** in the CI environment; `pip install pytest`
  was needed to run the suite (the package itself remains dependency-free).
- **Follow-up (optional)**: `__version__` was left at `0.2.0` since the
  release/bump process is owned by the pipeline; bump to `0.3.0` when the
  Unreleased section is cut.
