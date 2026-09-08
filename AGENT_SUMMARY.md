# Agent Summary

## What changed and why

This was a **feature pass**: add `TaskManager.clear_completed()` to
`tasking/manager.py`, plus focused tests, a changelog entry and README
documentation. The method removes every task whose `done` status is `True`
and returns the removed `Task` objects in insertion order; when nothing is
completed it returns `[]` and mutates nothing. Pending tasks are untouched
and keep their ids; the internal id counter is not reset (new tasks continue
the monotonic sequence, consistent with `remove()`'s existing behavior).

Design notes:

- Implemented in the existing API style: short one-liner docstring, typed
  signature (`-> list`), no external dependencies, no changes to any
  existing method, class or exception.
- Removal is a single pass: collect completed tasks in insertion order
  (dicts preserve insertion order in Python 3.7+), then delete by id. This
  guarantees the returned list is ordered by insertion and that `all()` /
  `pending()` keep their relative order for surviving tasks.
- `clear_completed()` never raises: unknown-id handling does not apply
  because it takes no arguments.

## Files added/modified

| File | Change |
|------|--------|
| `tasking/manager.py` | Added `clear_completed()` to `TaskManager` (9 lines, between `complete()` and `all()`) |
| `tests/test_clear_completed.py` | New: 9 focused tests — several completed removed; mixed completed/pending; empty manager; no-completed mutates nothing; pending survive with ids intact; insertion-order return; idempotency; id counter not reset; removed tasks really gone |
| `CHANGELOG.md` | New at repo root: `Unreleased` entry describing `clear_completed()`, plus prior v0.2.0/v0.1.0 history moved here from the README |
| `README.md` | Usage section: 3-line `clear_completed()` example; API reference table row; test count updated to 63; changelog section now links to `CHANGELOG.md` |
| `AGENT_SUMMARY.md` | This file |

Not modified: `tasking/__init__.py` (no new exports needed), existing tests
(`tests/test_manager.py`, `tests/test_manager_extended.py` — the
backwards-compatibility contract), `docs/USAGE.md`.

## How to verify

```bash
# 1. run the full suite (pytest required: pip install pytest)
python3 -m pytest tests/ -q
# -> 63 passed in 0.05s
#    (54 pre-existing + 9 new in tests/test_clear_completed.py)

# 2. run only the new focused tests
python3 -m pytest tests/test_clear_completed.py -q
# -> 9 passed

# 3. spot-check the documented behavior end-to-end
python3 -c "
from tasking import TaskManager
m = TaskManager()
a = m.add('a'); b = m.add('b'); c = m.add('c')
m.complete(a.id); m.complete(c.id)
removed = m.clear_completed()
assert removed == [a, c] and m.all() == [b]
assert m.clear_completed() == [] and m.all() == [b]
assert m.add('d').id == 4
print('clear_completed OK')
"
```

Latest run: **63 passed** (`python3 -m pytest tests/ -q`), Python 3.12.3,
pytest 9.1.1. The README's 3-line example was also executed verbatim as a
script and its assertions passed.

## Risks, assumptions, follow-ups

- **Assumption — return type**: the task says "returns the list of removed
  Task objects", so the return value is a plain `list` of `Task` (matching
  the style of `search()`/`by_priority()`/`pending()`), not a generator or
  tuple. The annotation is `-> list` for consistency with the rest of the
  module (which does not use `list[Task]` annotations internally).
- **Assumption — id counter**: `clear_completed()` does not reset or reuse
  ids; `_next_id` keeps increasing, mirroring `remove()`. Reusing freed ids
  would be a breaking change and was not requested.
- **Assumption — CHANGELOG scope**: the README previously carried the
  v0.2.0 changelog inline. Since the task asked for a root `CHANGELOG.md`
  with an `Unreleased` entry, the full history (v0.1.0, v0.2.0) was moved
  there and the README now links to it, keeping a single source of truth.
  The README's inline v0.2.0 section was kept as well to avoid breaking
  anything that links to it.
- **Risk — docs drift**: the README API table and CHANGELOG describe
  `clear_completed()`; if its signature or semantics change later, update
  both (plus `docs/USAGE.md` if extended there).
- **Risk — `datetime` due-date quirk (pre-existing, unchanged)**:
  `_validate_due_date` still accepts `datetime.datetime` objects, which makes
  `is_overdue()` raise `TypeError`. Out of scope for this task; documented in
  `docs/USAGE.md`; left as a follow-up.
- **pytest not preinstalled** in the CI environment; `pip install pytest`
  was needed to run the suite (the package itself remains dependency-free).
- **Not committed**: per the pipeline contract, all changes are left
  uncommitted in the working tree.
