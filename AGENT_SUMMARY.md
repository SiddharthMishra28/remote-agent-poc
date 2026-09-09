# Agent Summary — `complete_all()` pass

This file (replaces the previous `reschedule()` pass summary) documents the
changes made in this run: adding `TaskManager.complete_all()` to the `tasking`
package, focused tests, and the matching docs updates.

## What changed and why

1. **`tasking/manager.py`** — added `TaskManager.complete_all() -> list`
   directly after `complete()`. It returns
   `[self.complete(t.id) for t in self.pending()]`, i.e. it reuses the
   existing `complete()` path (same lookup, same in-place `done = True`
   mutation) for every currently-pending task. The return value contains
   exactly the tasks completed by *this* call, in insertion order
   (dict insertion order, same as `pending()`/`all()`); already-done tasks
   are excluded, so an empty or all-done manager yields `[]`. Typed
   (`-> list`, matching `clear_completed()`/`due_soon()`), one-line
   docstring, no new imports or dependencies.
2. **`tests/test_complete_all.py`** (new) — 9 focused pytest tests covering
   every required case: empty manager returns `[]`, all-done manager
   returns `[]` (and mutates nothing), mixed manager completes only the
   pending ones and returns exactly them in insertion order (including a
   task completed out of order beforehand), completed tasks report
   `done is True` afterwards, and `stats()` reflects all-completed after
   the call. Plus: returned objects are the same `Task` instances,
   idempotency (second call returns `[]`), and no removal / id-counter
   reset.
3. **`CHANGELOG.md`** — added the `complete_all()` entry and the new-tests
   bullet at the top of the `## Unreleased` section, following the existing
   format.
4. **`README.md`** — added a 2-line `complete_all()` example to the usage
   snippet (verified by executing it), a `complete_all` row in the API
   reference table, and refreshed the test-count line (126 → 135, including
   the 9 new `complete_all()` tests).

## Files added/modified

| File | Change |
|------|--------|
| `tasking/manager.py` | Modified — new `complete_all()` method after `complete()` |
| `tests/test_complete_all.py` | Added — 9 focused pytest tests |
| `CHANGELOG.md` | Modified — Unreleased entry for `complete_all()` + tests bullet |
| `README.md` | Modified — usage example, API table row, test counts |
| `AGENT_SUMMARY.md` | Replaced with this summary |

Not modified: `tasking/__init__.py` (no new exports needed —
`complete_all()` is a method on `TaskManager`), the existing tests,
`docs/USAGE.md`.

## How to verify

```bash
# 1. run the full suite (pytest must be installed: pip install pytest)
python3 -m pytest tests/ -q
# expected: 135 passed

# 2. run only the new complete_all tests
python3 -m pytest tests/test_complete_all.py -q
# expected: 9 passed

# 3. spot-check complete_all() semantics directly
python3 -c "
from tasking import TaskManager
m = TaskManager()
a = m.add('a'); b = m.add('b'); c = m.add('c')
m.complete(a.id)
done = m.complete_all()
print([t.title for t in done])   # ['b', 'c']
print(m.stats())                 # {'total': 3, 'pending': 0, 'completed': 3, 'overdue': 0}
print(m.complete_all())          # []
"
```

Latest run: **135 passed** (`python3 -m pytest tests/ -q`, Python 3.12.3,
pytest installed via `pip install pytest`) — 126 pre-existing tests
unchanged and green, plus 9 new `complete_all()` tests. The README usage
example's output was verified by executing the snippet directly.

## Risks, assumptions, follow-ups

- **Return value is "completed by this call", not "all done tasks".**
  Per the spec, already-done tasks are excluded from the return value;
  the method is idempotent (a second call returns `[]`). This is covered
  by dedicated tests.
- **Ordering is insertion order**, matching `pending()`, `all()` and
  `clear_completed()` (dict insertion order). A task completed
  out-of-order beforehand still appears in its original insertion
  position in the result — tested.
- **Reuses `complete()`** rather than mutating `done` directly, so the
  single internal path for marking tasks done is preserved (spec
  requirement 2). No behaviour of `complete()` changed.
- **No removal, no id-counter effect.** `complete_all()` only flips
  `done`; tasks remain in the manager and subsequent `add()` ids are
  unaffected — tested.
- **pytest is not preinstalled** in this CI environment; `pip install
  pytest` was needed to run the suite (the package itself remains
  dependency-free), same as in prior passes.
- **`__version__` stays `0.2.0`** — the new method ships under Unreleased,
  matching how `stats()`/`tag_counts()`/`due_soon()`/`reschedule()` were
  handled. Bump when the Unreleased section is cut.
- **Follow-up (optional)**: document `complete_all()` in `docs/USAGE.md`,
  which prior passes also left untouched.
