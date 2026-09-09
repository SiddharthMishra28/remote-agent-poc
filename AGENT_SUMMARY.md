# Agent Summary — `reschedule()` pass

This file (replaces the previous `due_soon()` pass summary) documents the
changes made in this run: adding `TaskManager.reschedule(task_id,
due_date=None, priority=None)` to the `tasking` package, focused tests, and
the matching docs updates.

## What changed and why

1. **`tasking/manager.py`** — added `TaskManager.reschedule(task_id,
   due_date=None, priority=None) -> Task`. It looks up the task by id
   (raising `TaskNotFoundError` for unknown ids, consistent with
   `complete()`/`remove()`), validates any provided field with the existing
   `_validate_due_date` / `_validate_priority` helpers (the same rules as
   `add()`), and updates only the fields explicitly provided — passing
   `None` for a field leaves it unchanged. It returns the updated `Task`
   (the same object, mutated in place). Validation is all-or-nothing: both
   provided fields are validated before either is assigned, so a failed
   validation leaves the task completely untouched. No new imports or
   dependencies were needed.
2. **`tests/test_reschedule.py`** (new) — 17 focused tests covering every
   required case: unknown id raises `TaskNotFoundError` (with and without
   args), no-arg call leaves the task unchanged and returns the same object,
   due-date-only update, priority-only update, both-at-once update,
   validation errors propagating (bad priority value → `ValueError`, bad
   priority type → `TypeError`, bad date string → `ValueError`, bad date
   type → `TypeError`), atomicity on validation failure (a bad field does
   not apply the other field), isolation from other tasks, and interaction
   with `stats()`/`is_overdue()` when rescheduling a task out of and into
   overdue. Margins are whole days away from today so the tests are
   deterministic.
3. **`CHANGELOG.md`** — added the `reschedule()` entry and the new-tests
   bullet to the `## Unreleased` section, following the existing format.
4. **`README.md`** — added a 2-line `reschedule()` example to the usage
   snippet (verified by executing it), a `reschedule` row in the API
   reference table, and refreshed the test-count line (109 → 126, including
   the 17 new `reschedule()` tests).

## Files added/modified

| File | Change |
|------|--------|
| `tasking/manager.py` | Modified — new `reschedule()` method after `complete()` |
| `tests/test_reschedule.py` | Added — 17 focused pytest tests |
| `CHANGELOG.md` | Modified — Unreleased entry for `reschedule()` + tests bullet |
| `README.md` | Modified — usage example, API table row, test counts |
| `AGENT_SUMMARY.md` | Replaced with this summary |

Not modified: `tasking/__init__.py` (no new exports needed — `reschedule()`
is a method on `TaskManager`), the existing tests, `docs/USAGE.md`.

## How to verify

```bash
# 1. run the full suite (pytest must be installed: pip install pytest)
python3 -m pytest tests/ -q
# expected: 126 passed

# 2. run only the new reschedule tests
python3 -m pytest tests/test_reschedule.py -q
# expected: 17 passed

# 3. spot-check reschedule() semantics directly
python3 -c "
from datetime import date, timedelta
from tasking import TaskManager
m = TaskManager()
t = m.add('Move', due_date=(date.today() + timedelta(days=1)).isoformat(), priority=0)
r = m.reschedule(t.id, due_date=(date.today() + timedelta(days=30)).isoformat(), priority=2)
print(r is t, r.due_date, r.priority)  # True <date+30d> 2
"
```

Latest run: **126 passed** (`python3 -m pytest tests/ -q`, Python 3.12.3,
pytest installed via `pip install pytest`) — 109 pre-existing tests
unchanged and green, plus 17 new `reschedule()` tests. The README usage
example's output was verified by executing the snippet directly.

## Risks, assumptions, follow-ups

- **`None` means "leave unchanged", not "clear".** Per the task spec,
  passing `None` for a field leaves it unchanged, so there is currently no
  way to clear a task's `due_date` back to `None` via `reschedule()`. This
  matches the spec exactly; if clearing is ever wanted, a sentinel (e.g.
  `due_date=...`) would be needed — a deliberate follow-up, not a bug.
- **Lookup happens before validation.** For an unknown id *and* an invalid
  field, `TaskNotFoundError` wins (consistent with `complete()`/`remove()`,
  which look up first). The required tests don't pin this ordering; it was
  chosen for consistency with the existing id-based methods.
- **All-or-nothing updates.** Both provided fields are validated before
  either is assigned, so a failed validation never leaves a half-updated
  task. This is stricter than "apply what you can" and is covered by two
  dedicated atomicity tests.
- **Completed tasks can be rescheduled.** `reschedule()` does not check
  `done`, mirroring `complete()`/`remove()` which also don't gate on state.
  Rescheduling a completed task updates its fields but never affects
  `stats()["overdue"]` (overdue counts pending tasks only) — tested.
- **pytest is not preinstalled** in this CI environment; `pip install
  pytest` was needed to run the suite (the package itself remains
  dependency-free), same as in prior passes.
- **`__version__` stays `0.2.0`** — the new method ships under Unreleased,
  matching how `stats()`/`tag_counts()`/`due_soon()` were handled. Bump when
  the Unreleased section is cut.
- **Follow-up (optional)**: document `reschedule()` in `docs/USAGE.md`,
  which prior passes also left untouched.
