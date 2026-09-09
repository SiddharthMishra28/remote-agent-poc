# Agent Summary

## What changed and why

This pass added a **`tag_counts()` method** to `TaskManager` in
`tasking/manager.py`, per the task requirements. The manager already had
`add`/`remove`/`complete`/`search`/`by_priority`/`all`/`pending`/
`clear_completed`/`stats`; `tag_counts()` was the only new behaviour
introduced — nothing existing was modified or removed.

1. **`tasking/manager.py`** — added `tag_counts() -> dict`:
   - Returns a dict mapping each distinct tag across **all** tasks (done
     and pending alike) to the number of tasks carrying it.
   - Counts tags exactly as stored by `add()`; tasks without tags are
     skipped; returns `{}` for an empty manager.
   - Style follows the existing API: typed return annotation, one-line
     docstring, pure stdlib, no external deps.
2. **`tests/test_manager_tag_counts.py`** — new focused test file
   (15 tests) covering everything the task required plus a few
   consistency checks: empty manager (`{}`), single tag, repeated tags
   across tasks, multiple distinct tags, multiple tags on one task,
   mixed repeated+distinct, tasks without tags skipped (incl. explicit
   `tags=[]`), combined done+pending counting, done-only counting,
   stored-tag semantics (stripped, case preserved), removal, plain-dict
   typing, manual-count agreement, and the README example.
3. **`CHANGELOG.md`** — added a `tag_counts()` entry (plus a note about
   the new tests) to the existing **Unreleased** section.
4. **`README.md`** — added the required 2-line `tag_counts()` example to
   the usage section (output verified by execution — see below), a
   `tag_counts()` row in the `TaskManager` API reference table, and
   refreshed the stale test counts (69 → 93; the previous summary's
   counts predated the `clear_completed()` tests).

## Files added/modified

| File | Change |
|------|--------|
| `tasking/manager.py` | Added `tag_counts()` method (6 lines, after `stats()`) |
| `tests/test_manager_tag_counts.py` | New: 15 focused `tag_counts()` tests |
| `CHANGELOG.md` | `tag_counts()` entry added under Unreleased |
| `README.md` | 2-line `tag_counts()` usage example, API table row, test count fix |
| `AGENT_SUMMARY.md` | This file (replaces the previous `stats()` pass summary) |

Not modified: `tasking/__init__.py` (no new exports needed —
`tag_counts()` is a method on `TaskManager`), the existing tests,
`docs/USAGE.md`.

## How to verify

```bash
# 1. run the full suite (pytest must be installed: pip install pytest)
python3 -m pytest tests/ -q
# expected: 93 passed

# 2. run only the new tag_counts tests
python3 -m pytest tests/test_manager_tag_counts.py -q
# expected: 15 passed

# 3. spot-check tag_counts() semantics directly
python3 -c "
from tasking import TaskManager
m = TaskManager()
m.add('Fix login bug', tags=['bug', 'auth'])
m.add('Add dark mode', tags=['feature'])
done = m.add('Shipped fix', tags=['bug'])
m.complete(done.id)
print(m.tag_counts())
# {'bug': 2, 'auth': 1, 'feature': 1} — done tasks are counted too
"
```

Latest run: **93 passed** (`python3 -m pytest tests/ -q`, Python 3.12.3,
pytest 9.1.1) — 78 pre-existing tests unchanged and green, plus 15 new
`tag_counts()` tests. The README usage example's output comment was
verified by executing the snippet (an initial draft included a tag that
the README flow removes; corrected after this verification caught it,
and the README-example test mirrors the README exactly).

## Risks, assumptions, follow-ups

- **Ambiguity — "stripped and lowercased"**: the task said tags already
  come back from `add()` "stripped and lowercased", but the actual
  `add()` implementation (`_validate_tags` in `tasking/manager.py`)
  only *strips*; case is preserved, and `docs/USAGE.md` explicitly
  documents `["Work", "work"]` as two accepted distinct tags. Per the
  "make the most reasonable choice and document it" instruction,
  `tag_counts()` counts tags **exactly as stored** (stripped,
  case-preserved), so `'Work'` and `'work'` are separate keys. This is
  the backwards-compatible reading — lowercasing keys would silently
  merge tags the existing API deliberately keeps distinct. Pinned by
  `test_tag_counts_uses_stored_tags_no_mutation`. Follow-up (optional):
  if lowercase normalization is ever wanted, it should be added to
  `add()` itself, not here.
- **Assumption — test-count doc drift**: README claimed 69 tests while
  the suite had 78 (the `clear_completed()` tests were never counted);
  fixed to 93 in the same edit pass.
- **Risk — `Task` constructed directly bypasses validation**, so a
  hand-built `Task(tags=[...])` with un-normalized values would be
  counted verbatim by `tag_counts()`. Inherent to the existing design
  (only `TaskManager.add` validates) and out of scope.
- **pytest was not preinstalled** in the CI environment;
  `pip install pytest` was needed to run the suite (the package itself
  remains dependency-free).
- **Follow-up (optional)**: `__version__` stays at `0.2.0`; bump when
  the Unreleased section (stats + clear_completed + tag_counts) is cut.
