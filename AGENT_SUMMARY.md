# Agent Summary

## What changed and why

Added a `stats()` method to `TaskManager` in `tasking/manager.py`, giving a
one-call snapshot of the manager's state. The task asked for a typed,
dependency-free method consistent with the existing API style, plus tests,
changelog and README coverage.

**Semantics implemented** (per the task spec):

- `total` — all tasks in the manager.
- `pending` — tasks where `done is False`.
- `completed` — tasks where `done is True`.
- `overdue` — **pending** tasks whose `due_date` is strictly in the past,
  determined via the existing `Task.is_overdue()`. Consequences:
  - a task due **today** is **not** overdue (boundary, matches
    `is_overdue()`'s `due_date < date.today()` comparison);
  - a **completed** task with a past due date is **not** counted as overdue
    (the task spec says "overdue = pending tasks whose due_date is in the
    past");
  - tasks without a due date are never overdue.

**Design choices:**

- `stats()` computes `pending` once and derives `completed` as
  `total - pending`, so the counts are always internally consistent
  (`total == pending + completed`).
- Typed with `-> dict` and a one-line docstring, matching the style of
  `is_overdue()` / `to_dict()`. No new imports, no external dependencies.
- The module docstring's feature list gained a `stats()` line, mirroring how
  every other feature is listed.

## Files added/modified

| File | Change |
|------|--------|
| `tasking/manager.py` | Added `TaskManager.stats()` (7 lines) + one line in the module docstring feature list |
| `tests/test_manager_stats.py` | **New** — 11 focused tests for `stats()` (see below) |
| `CHANGELOG.md` | **New** — created with an `Unreleased` section documenting `stats()` (the repo had no CHANGELOG; the v0.2.0 history from the README is included below it for continuity) |
| `README.md` | Added the 2-line `stats()` example to the usage section, a `stats` row in the API reference table, an Unreleased changelog pointer, and updated the test count |
| `AGENT_SUMMARY.md` | This file |

**Test coverage in `tests/test_manager_stats.py`** (plain pytest functions,
no classes, per repo convention):

- empty manager → all four counts are 0
- exact key set (`{'total', 'pending', 'completed', 'overdue'}`)
- mixed states (done/pending × overdue/future/no-due-date)
- completed-but-overdue task is **not** counted in `overdue`
- tasks without due dates are never overdue
- boundary: due **today** → not overdue; due **yesterday** → overdue
- `datetime.date` objects as due dates (not just ISO strings)
- stats reflect removals
- all counts are `int`s

## How to verify

```bash
# pytest is not preinstalled in this environment
pip install pytest

# full suite (65 tests: 2 original + 52 extended + 11 stats)
python3 -m pytest tests/ -q
# expected: "65 passed"

# quick manual check
python3 -c "
from datetime import date, timedelta
from tasking import TaskManager
m = TaskManager()
m.add('late', due_date=(date.today()-timedelta(days=1)).isoformat())
m.add('today', due_date=date.today())
m.add('ok')
t = m.add('done late', due_date=(date.today()-timedelta(days=9)).isoformat())
m.complete(t.id)
print(m.stats())
# {'total': 4, 'pending': 3, 'completed': 1, 'overdue': 1}
"
```

**Latest run: `65 passed` in 0.05s** (Python 3.12.3, pytest 9.1.1). The
README's `stats()` example output was executed and asserted before being
written into the docs.

## Risks, assumptions, follow-ups

- **Assumption — completed tasks are excluded from `overdue`.** The task
  spec says "overdue = pending tasks whose due_date is in the past", so a
  done task with a past due date counts only toward `completed`. This
  intentionally differs from `Task.is_overdue()`, which ignores `done` state;
  a test pins this distinction explicitly.
- **Assumption — CHANGELOG.md did not exist** (the v0.2.0 history lived only
  in README.md). Created it with an `Unreleased` section at the top, and
  copied the v0.2.0 entry below it so the file is a complete history. The
  README now links to it.
- **Risk — day-boundary flakiness:** `stats()` (like `is_overdue()`) compares
  against `date.today()` at call time. Tests that construct "yesterday /
  today" tasks could theoretically flake if executed exactly across local
  midnight; this is inherent to the existing `is_overdue()` design and not
  introduced by this change.
- **Risk — docs drift:** the README quotes `stats()` output verbatim; if the
  key set ever changes, the README/API table must be updated (the new tests
  will fail first, which is the intended safety net).
- **Follow-up (pre-existing, not addressed):** `_validate_due_date` accepts
  `datetime.datetime` objects (they subclass `date`) but stores them
  unconverted, after which `is_overdue()` — and therefore `stats()` — raises
  `TypeError`. Documented in `docs/USAGE.md`; fixing it is out of scope here.
- **Follow-up:** `stats()` could later grow richer breakdowns (e.g. per
  priority or per tag); kept to the four specified keys to match the task
  contract exactly.
