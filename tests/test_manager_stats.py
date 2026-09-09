"""Focused tests for TaskManager.stats()."""

from datetime import date, timedelta

from tasking import TaskManager


def _iso(d):
    return d.isoformat()


def test_stats_on_empty_manager_all_zero():
    assert TaskManager().stats() == {
        "total": 0,
        "pending": 0,
        "completed": 0,
        "overdue": 0,
    }


def test_stats_returns_exactly_the_four_documented_keys():
    m = TaskManager()
    m.add("a")
    assert set(m.stats()) == {"total", "pending", "completed", "overdue"}


def test_stats_mixed_states():
    m = TaskManager()
    past = _iso(date.today() - timedelta(days=1))
    future = _iso(date.today() + timedelta(days=1))

    done_overdue = m.add("done and overdue", due_date=past)
    done_future = m.add("done and future", due_date=future)
    m.add("pending and overdue", due_date=past)
    m.add("pending and future", due_date=future)
    m.add("pending, no due date")

    m.complete(done_overdue.id)
    m.complete(done_future.id)

    assert m.stats() == {
        "total": 5,
        "pending": 3,
        "completed": 2,
        "overdue": 1,  # only the *pending* overdue task counts
    }


def test_stats_completed_overdue_task_is_not_overdue():
    m = TaskManager()
    t = m.add("late but done", due_date=_iso(date.today() - timedelta(days=5)))
    m.complete(t.id)
    assert t.is_overdue() is True  # Task-level check ignores done...
    assert m.stats()["overdue"] == 0  # ...but stats() counts only pending


def test_stats_tasks_without_due_dates_never_overdue():
    m = TaskManager()
    m.add("no due date, pending")
    m.add("another one")
    stats = m.stats()
    assert stats == {"total": 2, "pending": 2, "completed": 0, "overdue": 0}


def test_stats_with_and_without_due_dates_mixed():
    m = TaskManager()
    m.add("past due", due_date=_iso(date.today() - timedelta(days=2)))
    m.add("due today", due_date=_iso(date.today()))
    m.add("due next week", due_date=_iso(date.today() + timedelta(days=7)))
    m.add("no due date")
    assert m.stats() == {
        "total": 4,
        "pending": 4,
        "completed": 0,
        "overdue": 1,
    }


def test_stats_boundary_due_today_is_not_overdue():
    m = TaskManager()
    m.add("due today", due_date=_iso(date.today()))
    assert m.stats() == {"total": 1, "pending": 1, "completed": 0, "overdue": 0}


def test_stats_boundary_due_yesterday_is_overdue():
    m = TaskManager()
    m.add("due yesterday", due_date=_iso(date.today() - timedelta(days=1)))
    assert m.stats() == {"total": 1, "pending": 1, "completed": 0, "overdue": 1}


def test_stats_accepts_date_objects_too():
    m = TaskManager()
    m.add("late", due_date=date.today() - timedelta(days=1))
    m.add("today", due_date=date.today())
    assert m.stats()["overdue"] == 1


def test_stats_reflects_removals():
    m = TaskManager()
    t = m.add("late", due_date=_iso(date.today() - timedelta(days=1)))
    m.add("fine")
    assert m.stats() == {"total": 2, "pending": 2, "completed": 0, "overdue": 1}
    m.remove(t.id)
    assert m.stats() == {"total": 1, "pending": 1, "completed": 0, "overdue": 0}


def test_stats_counts_are_ints():
    m = TaskManager()
    m.add("a")
    for value in m.stats().values():
        assert isinstance(value, int)
