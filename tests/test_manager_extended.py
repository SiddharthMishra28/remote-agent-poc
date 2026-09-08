"""Extended tests for the hardened tasking package.

Covers: input validation, remove(), search(), due dates, priorities,
is_overdue(), to_dict() and edge cases. Existing tests in
tests/test_manager.py remain the backwards-compatibility contract.
"""

import json
from datetime import date, timedelta

import pytest

from tasking import Task, TaskManager, TaskNotFoundError
from tasking.manager import TaskNotFoundError as TNFE


# ---------------------------------------------------------------------------
# title validation
# ---------------------------------------------------------------------------


def test_add_rejects_empty_title():
    with pytest.raises(ValueError, match="title must not be empty"):
        TaskManager().add("")


def test_add_rejects_whitespace_title():
    for bad in ("   ", "\t", "\n  \n"):
        with pytest.raises(ValueError, match="title must not be empty"):
            TaskManager().add(bad)


def test_add_rejects_non_string_title():
    with pytest.raises(TypeError, match="title must be a string"):
        TaskManager().add(123)
    with pytest.raises(TypeError, match="title must be a string"):
        TaskManager().add(None)


def test_add_strips_title_whitespace():
    m = TaskManager()
    t = m.add("  write docs  ")
    assert t.title == "write docs"


# ---------------------------------------------------------------------------
# tags validation
# ---------------------------------------------------------------------------


def test_add_rejects_duplicate_tags():
    with pytest.raises(ValueError, match="duplicate tag"):
        TaskManager().add("t", tags=["work", "work"])


def test_add_rejects_duplicate_tags_after_stripping():
    with pytest.raises(ValueError, match="duplicate tag"):
        TaskManager().add("t", tags=["work", " work "])


def test_add_rejects_non_string_tag():
    with pytest.raises(TypeError, match="each tag must be a string"):
        TaskManager().add("t", tags=["ok", 1])


def test_add_rejects_tags_as_bare_string():
    with pytest.raises(TypeError, match="not a single string"):
        TaskManager().add("t", tags="work")


def test_add_rejects_empty_tag():
    with pytest.raises(ValueError, match="tags must not be empty"):
        TaskManager().add("t", tags=["ok", "   "])


def test_add_rejects_non_iterable_tags():
    with pytest.raises(TypeError, match="tags must be a list"):
        TaskManager().add("t", tags=42)


def test_add_accepts_tuple_and_set_tags():
    m = TaskManager()
    assert m.add("t", tags=("a", "b")).tags == ["a", "b"]
    assert sorted(m.add("t2", tags={"x", "y"}).tags) == ["x", "y"]


def test_add_tags_are_stripped():
    t = TaskManager().add("t", tags=[" work "])
    assert t.tags == ["work"]


def test_add_default_tags_not_shared_between_tasks():
    m = TaskManager()
    a = m.add("a")
    b = m.add("b")
    a.tags.append("mutated")
    assert b.tags == []


# ---------------------------------------------------------------------------
# due date validation and storage
# ---------------------------------------------------------------------------


def test_add_rejects_malformed_due_date():
    for bad in ("2026-13-01", "2026-02-30", "not-a-date", "01-02-2026",
                "2026/01/02", "20260101", "2026-1-2"):
        with pytest.raises(ValueError, match="not a valid ISO-8601 date"):
            TaskManager().add("t", due_date=bad)


def test_add_rejects_non_string_non_date_due_date():
    with pytest.raises(TypeError, match="due_date must be an ISO-8601"):
        TaskManager().add("t", due_date=20260101)
    with pytest.raises(TypeError, match="due_date must be an ISO-8601"):
        TaskManager().add("t", due_date=True)


def test_add_stores_due_date_as_date():
    t = TaskManager().add("t", due_date="2026-12-25")
    assert t.due_date == date(2026, 12, 25)


def test_add_accepts_date_object_due_date():
    t = TaskManager().add("t", due_date=date(2026, 12, 25))
    assert t.due_date == date(2026, 12, 25)


def test_add_due_date_defaults_to_none():
    assert TaskManager().add("t").due_date is None


# ---------------------------------------------------------------------------
# priority validation and by_priority
# ---------------------------------------------------------------------------


def test_add_rejects_priority_out_of_range():
    for bad in (-1, 4, 100):
        with pytest.raises(ValueError, match="priority must be in 0-3"):
            TaskManager().add("t", priority=bad)


def test_add_rejects_non_int_priority():
    with pytest.raises(TypeError, match="priority must be an int"):
        TaskManager().add("t", priority="1")
    with pytest.raises(TypeError, match="priority must be an int"):
        TaskManager().add("t", priority=1.5)
    with pytest.raises(TypeError, match="priority must be an int"):
        TaskManager().add("t", priority=True)


def test_add_priority_defaults_to_zero():
    assert TaskManager().add("t").priority == 0


def test_by_priority_filters():
    m = TaskManager()
    low = m.add("low", priority=0)
    mid = m.add("mid", priority=2)
    m.add("high", priority=3)
    assert m.by_priority(0) == [low]
    assert m.by_priority(2) == [mid]
    assert m.by_priority(1) == []


def test_by_priority_validates_argument():
    with pytest.raises(ValueError, match="priority must be in 0-3"):
        TaskManager().by_priority(9)
    with pytest.raises(TypeError, match="priority must be an int"):
        TaskManager().by_priority("high")


def test_by_priority_accepts_all_levels():
    m = TaskManager()
    for p in range(4):
        m.add(f"p{p}", priority=p)
    for p in range(4):
        assert [t.title for t in m.by_priority(p)] == [f"p{p}"]


# ---------------------------------------------------------------------------
# remove()
# ---------------------------------------------------------------------------


def test_remove_returns_removed_task():
    m = TaskManager()
    t = m.add("gone")
    removed = m.remove(t.id)
    assert removed is t
    assert m.all() == []


def test_remove_missing_raises_task_not_found():
    m = TaskManager()
    with pytest.raises(TaskNotFoundError):
        m.remove(999)


def test_remove_twice_raises_second_time():
    m = TaskManager()
    t = m.add("once")
    m.remove(t.id)
    with pytest.raises(TaskNotFoundError):
        m.remove(t.id)


def test_remove_does_not_disturb_other_tasks():
    m = TaskManager()
    a = m.add("a")
    b = m.add("b")
    m.remove(a.id)
    assert m.all() == [b]


def test_task_not_found_error_carries_id_and_message():
    err = TaskNotFoundError(42)
    assert err.task_id == 42
    assert "42" in str(err)


def test_task_not_found_error_importable_from_manager_module():
    # both import paths must be the same exception class
    assert TNFE is TaskNotFoundError


def test_complete_missing_raises_task_not_found():
    with pytest.raises(TaskNotFoundError):
        TaskManager().complete(1)


# ---------------------------------------------------------------------------
# search()
# ---------------------------------------------------------------------------


def test_search_is_case_insensitive():
    m = TaskManager()
    m.add("Write Docs")
    m.add("write more docs")
    m.add("unrelated")
    hits = m.search("WRITE")
    assert [t.title for t in hits] == ["Write Docs", "write more docs"]


def test_search_is_substring_not_prefix_only():
    m = TaskManager()
    t = m.add("preparation notes")
    assert m.search("ration") == [t]


def test_search_no_match_returns_empty_list():
    m = TaskManager()
    m.add("one")
    assert m.search("zzz") == []


def test_search_matches_all_on_empty_query():
    m = TaskManager()
    m.add("one")
    m.add("two")
    assert len(m.search("")) == 2
    assert len(m.search("   ")) == 2


def test_search_ignores_surrounding_whitespace_in_query():
    m = TaskManager()
    t = m.add("write docs")
    assert m.search("  write  ") == [t]


def test_search_rejects_non_string_query():
    with pytest.raises(TypeError, match="query must be a string"):
        TaskManager().search(5)
    with pytest.raises(TypeError, match="query must be a string"):
        TaskManager().search(None)


def test_search_on_empty_manager():
    assert TaskManager().search("anything") == []


# ---------------------------------------------------------------------------
# is_overdue()
# ---------------------------------------------------------------------------


def _task_with_due(due):
    return Task(id=1, title="t", due_date=due)


def test_is_overdue_true_for_past_due_date():
    past = date.today() - timedelta(days=1)
    assert _task_with_due(past).is_overdue() is True


def test_is_overdue_false_for_future_due_date():
    future = date.today() + timedelta(days=1)
    assert _task_with_due(future).is_overdue() is False


def test_is_overdue_false_for_due_today():
    assert _task_with_due(date.today()).is_overdue() is False


def test_is_overdue_false_without_due_date():
    assert _task_with_due(None).is_overdue() is False


def test_is_overdue_via_manager_add():
    m = TaskManager()
    overdue = m.add("late", due_date=(date.today() - timedelta(days=2)).isoformat())
    ok = m.add("fine", due_date=(date.today() + timedelta(days=2)).isoformat())
    assert overdue.is_overdue() is True
    assert ok.is_overdue() is False


# ---------------------------------------------------------------------------
# to_dict()
# ---------------------------------------------------------------------------


def test_to_dict_full_shape():
    t = TaskManager().add(
        "  ship it  ",
        due_date="2026-12-25",
        tags=["release", "q4"],
        priority=3,
    )
    assert t.to_dict() == {
        "id": 1,
        "title": "ship it",
        "done": False,
        "tags": ["release", "q4"],
        "due_date": "2026-12-25",
        "priority": 3,
    }


def test_to_dict_defaults():
    d = TaskManager().add("plain").to_dict()
    assert d == {
        "id": 1,
        "title": "plain",
        "done": False,
        "tags": [],
        "due_date": None,
        "priority": 0,
    }


def test_to_dict_is_json_serializable():
    t = TaskManager().add("json", due_date="2026-01-31", tags=["x"])
    assert json.loads(json.dumps(t.to_dict()))["due_date"] == "2026-01-31"


def test_to_dict_tags_is_a_copy():
    t = TaskManager().add("t", tags=["a"])
    d = t.to_dict()
    d["tags"].append("b")
    assert t.tags == ["a"]


def test_to_dict_reflects_done_state():
    m = TaskManager()
    t = m.add("t")
    m.complete(t.id)
    assert t.to_dict()["done"] is True


# ---------------------------------------------------------------------------
# edge cases & integration
# ---------------------------------------------------------------------------


def test_ids_keep_increasing_after_remove():
    m = TaskManager()
    a = m.add("a")
    m.remove(a.id)
    b = m.add("b")
    assert b.id == a.id + 1


def test_add_signature_backwards_compatible_keywords():
    # the pre-existing keyword call style must keep working
    m = TaskManager()
    t = m.add("write docs", tags=["docs"])
    assert t.tags == ["docs"]
    assert m.complete(t.id).done


def test_full_workflow():
    m = TaskManager()
    bug = m.add("Fix login bug", due_date="2020-01-01", tags=["bug"], priority=3)
    feat = m.add("Add dark mode", due_date="2030-01-01", tags=["feat"], priority=1)
    m.complete(bug.id)

    assert len(m.all()) == 2
    assert len(m.pending()) == 1
    assert m.pending() == [feat]
    assert m.search("DARK") == [feat]
    assert m.by_priority(3) == [bug]
    assert bug.is_overdue() is True
    assert feat.is_overdue() is False

    m.remove(bug.id)
    assert m.all() == [feat]
    with pytest.raises(TaskNotFoundError):
        m.remove(bug.id)


def test_task_dataclass_defaults_are_independent():
    a = Task(id=1, title="a")
    b = Task(id=2, title="b")
    a.tags.append("x")
    assert b.tags == []
    assert b.due_date is None
    assert b.priority == 0
    assert b.done is False
