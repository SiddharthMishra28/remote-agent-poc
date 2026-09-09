"""Focused tests for TaskManager.stats().

Covers: empty manager (all zeros), mixed done/pending states, tasks with
and without due dates, and the boundary where a task due today is NOT
overdue. Existing tests elsewhere remain the backwards-compatibility
contract.
"""

from datetime import date, timedelta

from tasking import TaskManager


def _iso(d):
    return d.isoformat()


# ---------------------------------------------------------------------------
# empty manager
# ---------------------------------------------------------------------------


def test_stats_on_empty_manager_all_zero():
    assert TaskManager().stats() == {
        "total": 0,
        "pending": 0,
        "completed": 0,
        "overdue": 0,
    }


def test_stats_keys_are_exactly_the_four_documented():
    assert set(TaskManager().stats()) == {
        "total",
        "pending",
        "completed",
        "overdue",
    }


# ---------------------------------------------------------------------------
# mixed states
# ---------------------------------------------------------------------------


def test_stats_counts_pending_and_completed():
    m = TaskManager()
    a = m.add("a")
    b = m.add("b")
    m.add("c")
    m.complete(a.id)
    m.complete(b.id)
    assert m.stats() == {
        "total": 3,
        "pending": 1,
        "completed": 2,
        "overdue": 0,
    }


def test_stats_all_completed():
    m = TaskManager()
    t = m.add("only")
    m.complete(t.id)
    assert m.stats() == {
        "total": 1,
        "pending": 0,
        "completed": 1,
        "overdue": 0,
    }


def test_stats_total_equals_pending_plus_completed():
    m = TaskManager()
    m.add("no due date")
    m.add("past", due_date=_iso(date.today() - timedelta(days=1)))
    m.add("today", due_date=_iso(date.today()))
    m.add("future", due_date=_iso(date.today() + timedelta(days=5)))
    done = m.add("done future", due_date=_iso(date.today() + timedelta(days=5)))
    m.complete(done.id)
    s = m.stats()
    assert s["total"] == s["pending"] + s["completed"] == 5


def test_stats_reflects_removal():
    m = TaskManager()
    t = m.add("gone")
    m.remove(t.id)
    assert m.stats()["total"] == 0


# ---------------------------------------------------------------------------
# tasks with and without due dates
# ---------------------------------------------------------------------------


def test_stats_overdue_counts_only_pending_past_due_tasks():
    m = TaskManager()
    m.add("overdue", due_date=_iso(date.today() - timedelta(days=2)))
    m.add("future", due_date=_iso(date.today() + timedelta(days=2)))
    m.add("no due date")
    assert m.stats() == {
        "total": 3,
        "pending": 3,
        "completed": 0,
        "overdue": 1,
    }


def test_stats_completed_past_due_task_is_not_overdue():
    m = TaskManager()
    late = m.add("late but done", due_date=_iso(date.today() - timedelta(days=2)))
    m.complete(late.id)
    assert late.is_overdue() is True  # is_overdue() ignores done state
    assert m.stats() == {
        "total": 1,
        "pending": 0,
        "completed": 1,
        "overdue": 0,  # ...but stats() only counts pending tasks as overdue
    }


def test_stats_task_without_due_date_is_never_overdue():
    m = TaskManager()
    m.add("no due date")
    assert m.stats()["overdue"] == 0


def test_stats_multiple_overdue_tasks():
    m = TaskManager()
    m.add("late 1", due_date=_iso(date.today() - timedelta(days=1)))
    m.add("late 2", due_date=_iso(date.today() - timedelta(days=30)))
    m.add("late 3", due_date=date.today() - timedelta(days=1))  # date object
    assert m.stats()["overdue"] == 3


# ---------------------------------------------------------------------------
# boundary: due today is NOT overdue
# ---------------------------------------------------------------------------


def test_stats_due_today_is_not_overdue():
    m = TaskManager()
    m.add("due today", due_date=_iso(date.today()))
    assert m.stats() == {
        "total": 1,
        "pending": 1,
        "completed": 0,
        "overdue": 0,
    }


def test_stats_boundary_mix_of_today_and_yesterday():
    m = TaskManager()
    m.add("due today", due_date=_iso(date.today()))
    m.add("due yesterday", due_date=_iso(date.today() - timedelta(days=1)))
    assert m.stats()["overdue"] == 1


def test_stats_due_today_as_date_object_is_not_overdue():
    m = TaskManager()
    m.add("due today", due_date=date.today())
    assert m.stats()["overdue"] == 0


# ---------------------------------------------------------------------------
# consistency with the rest of the API
# ---------------------------------------------------------------------------


def test_stats_agrees_with_all_pending_and_is_overdue():
    m = TaskManager()
    m.add("plain")
    m.add("past", due_date=_iso(date.today() - timedelta(days=1)))
    m.add("today", due_date=_iso(date.today()))
    m.add("future", due_date=_iso(date.today() + timedelta(days=1)))
    done = m.add("done past", due_date=_iso(date.today() - timedelta(days=1)))
    m.complete(done.id)

    s = m.stats()
    assert s["total"] == len(m.all())
    assert s["pending"] == len(m.pending())
    assert s["completed"] == len(m.all()) - len(m.pending())
    assert s["overdue"] == len([t for t in m.pending() if t.is_overdue()])


def test_stats_returns_plain_dict_of_ints():
    m = TaskManager()
    m.add("t")
    s = m.stats()
    assert isinstance(s, dict)
    assert all(isinstance(v, int) for v in s.values())
