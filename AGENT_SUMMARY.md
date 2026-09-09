# Agent Summary — `due_soon()` pass

This file (replaces the previous `tag_counts()` pass summary) documents the
changes made in this run: adding `TaskManager.due_soon(hours=48)` to the
`tasking` package, focused tests, and the matching docs updates.

## What changed and why

1. **`tasking/manager.py`** — added `TaskManager.due_soon(hours=48)`. It
   returns the list of pending (not done) tasks whose `due_date` is set and
   falls in the inclusive window `[today, today + hours]`, sorted by
   `due_date` ascending (soonest first). Overdue tasks (due strictly before
   today) and tasks without a due date are excluded. The `timedelta` import
   was added to support the window arithmetic. `hours` is validated eagerly
   (matching the codebase's `_validate_*` ethos): non-numeric values
   (including `bool`) raise `TypeError`, negative values raise `ValueError`.
2. **`tests/test_due_soon.py`** (new) — 16 focused tests covering all six
   required cases (empty manager, done excluded, no-due-date excluded,
   overdue excluded, well-inside-window included, well-beyond-window
   excluded) plus the inclusive 48-hour boundary, soonest-first ordering,
   insertion-order stability for same-date tasks, custom `hours` windows
   (widening and `hours=0`), ISO-string and date-object inputs, consistency
   with `pending()` + a manual filter, and argument validation. Margins are
   whole days away from the boundaries so the tests are deterministic.
3. **`CHANGELOG.md`** — added the `due_soon()` entry and the new-tests
   bullet to the `## Unreleased` section, following the existing format.
4. **`README.md`** — added a 2-line `due_soon()` example to the usage
   snippet (verified by executing it), a `due_soon` row in the API reference
   table, and refreshed the test-count line (93 → 109, including the 16 new
   `due_soon()` tests).

## Files added/modified

| File | Change |
|------|--------|
| `tasking/manager.py` | Modified — `timedelta` import; new `due_soon()` method after `tag_counts()` |
| `tests/test_due_soon.py` | Added — 16 focused pytest tests |
| `CHANGELOG.md` | Modified — Unreleased entry for `due_soon()` + tests bullet |
| `README.md` | Modified — usage example, API table row, test counts |

Not modified: `tasking/__init__.py` (no new exports needed — `due_soon()` is
a method on `TaskManager`), the existing tests, `docs/USAGE.md`.

## How to verify

```bash
# 1. run the full suite (pytest must be installed: pip install pytest)
python3 -m pytest tests/ -q
# expected: 109 passed

# 2. run only the new due_soon tests
python3 -m pytest tests/test_due_soon.py -q
# expected: 16 passed

# 3. spot-check due_soon() semantics directly
python3 -c "
from datetime import date, timedelta
from tasking import TaskManager
m = TaskManager()
m.add('Deploy hotfix', due_date=(date.today() + timedelta(days=1)).isoformat())
m.add('Far future', due_date=(date.today() + timedelta(days=30)).isoformat())
print([t.title for t in m.due_soon()])  # ['Deploy hotfix']
"
```

Latest run: **109 passed** (`python3 -m pytest tests/ -q`, Python 3.12.3,
pytest 9.1.1) — 93 pre-existing tests unchanged and green, plus 16 new
`due_soon()` tests. The README usage example's output was verified by
executing the snippet directly (returns `['Deploy hotfix']`).

## Risks, assumptions, follow-ups

- **"Now" is `date.today()`, not `datetime.now()`.** `due_date` is stored as
  a `datetime.date` (no time component), and comparing a `date` to a
  `datetime` raises `TypeError` (a documented edge case in `docs/USAGE.md`).
  The window is therefore day-granular: `date + timedelta(hours=hours)`
  truncates to whole days, so e.g. `hours=36` behaves like `hours=24` and
  `hours=0.5` behaves like `hours=0` (deadline == today). With the default
  48 hours this means tasks due today, tomorrow or the day after tomorrow
  are all included. This interpretation is assumed per the task's
  "inclusive window" wording.
- **`hours` validation was added** (TypeError/ValueError) although the task
  did not explicitly require it — it matches the codebase's eager-validation
  style and is covered by tests. `bool` is rejected as a number, consistent
  with Python treating `bool` as an `int` subclass.
- **`sorted()` is stable**, so tasks sharing the same `due_date` keep
  insertion order — tested explicitly.
- **pytest is not preinstalled** in this CI environment; `pip install
  pytest` was needed to run the suite (the package itself remains
  dependency-free), same as in prior passes.
- **`__version__` stays `0.2.0`** — the new method ships under Unreleased,
  matching how `stats()`/`tag_counts()` were handled. Bump when the
  Unreleased section is cut.
- **Follow-up (optional)**: document `due_soon()` in `docs/USAGE.md`, which
  prior passes also left untouched.
