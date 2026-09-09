"""Focused tests for TaskManager.reschedule(): in-place due_date/priority updates."""

from datetime import date, timedelta

from tasking import TaskManager, TaskNotFoundError


def _iso(d):
    """Format a date as the ISO string accepted by TaskManager.add()."""
    return d.isoformat()


# --- unknown id ------------------------------------------------------------


def test_reschedule_unknown_id_raises_task_not_found():
    m = TaskManager()
    try:
        m.reschedule(999)
    except TaskNotFoundError as e:
        assert e.task_id == 999
    else:
        raise AssertionError("expected TaskNotFoundError for unknown id")


def test_reschedule_unknown_id_with_args_still_raises():
    m = TaskManager()
    try:
        m.reschedule(42, due_date=_iso(date.today()), priority=2)
    except TaskNotFoundError:
        pass
    else:
        raise AssertionError("expected TaskNotFoundError for unknown id")


# --- no-op call -------------------------------------------------------------


def test_reschedule_no_args_leaves_task_unchanged_and_returns_it():
    m = TaskManager()
    t = m.add("Stable task", due_date=_iso(date.today() + timedelta(days=5)), priority=2)
    before_due = t.due_date
    before_priority = t.priority
    result = m.reschedule(t.id)
    assert result is t
    assert result.due_date == before_due
    assert result.priority == before_priority
    assert result.title == "Stable task"
    assert result.done is False


# --- due_date-only ----------------------------------------------------------


def test_reschedule_due_date_only_updates_due_date():
    m = TaskManager()
    t = m.add("Move deadline", due_date=_iso(date.today() + timedelta(days=1)), priority=1)
    new_due = date.today() + timedelta(days=10)
    result = m.reschedule(t.id, due_date=_iso(new_due))
    assert result is t
    assert result.due_date == new_due
    assert result.priority == 1  # unchanged


def test_reschedule_due_date_accepts_date_object():
    m = TaskManager()
    t = m.add("Date object", due_date=_iso(date.today()))
    new_due = date.today() + timedelta(days=3)
    result = m.reschedule(t.id, due_date=new_due)
    assert result.due_date == new_due


# --- priority-only ----------------------------------------------------------


def test_reschedule_priority_only_updates_priority():
    m = TaskManager()
    t = m.add("Bump priority", due_date=_iso(date.today() + timedelta(days=2)), priority=0)
    result = m.reschedule(t.id, priority=3)
    assert result is t
    assert result.priority == 3
    assert result.due_date == date.today() + timedelta(days=2)  # unchanged


# --- both at once -----------------------------------------------------------


def test_reschedule_both_fields_updates_both():
    m = TaskManager()
    t = m.add("Both", due_date=_iso(date.today() + timedelta(days=1)), priority=0)
    new_due = date.today() + timedelta(days=30)
    result = m.reschedule(t.id, due_date=_iso(new_due), priority=2)
    assert result is t
    assert result.due_date == new_due
    assert result.priority == 2


# --- validation errors ------------------------------------------------------


def test_reschedule_bad_priority_value_raises_value_error():
    m = TaskManager()
    t = m.add("Bad priority value", priority=1)
    try:
        m.reschedule(t.id, priority=5)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for priority out of range")
    assert t.priority == 1  # unchanged after failed validation


def test_reschedule_bad_priority_type_raises_type_error():
    m = TaskManager()
    t = m.add("Bad priority type", priority=1)
    try:
        m.reschedule(t.id, priority="high")
    except TypeError:
        pass
    else:
        raise AssertionError("expected TypeError for non-int priority")
    assert t.priority == 1


def test_reschedule_bad_date_string_raises_value_error():
    m = TaskManager()
    t = m.add("Bad date", due_date=_iso(date.today()))
    try:
        m.reschedule(t.id, due_date="2026-02-30")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for invalid date string")
    assert t.due_date == date.today()  # unchanged


def test_reschedule_bad_date_type_raises_type_error():
    m = TaskManager()
    t = m.add("Bad date type", due_date=_iso(date.today()))
    try:
        m.reschedule(t.id, due_date=12345)
    except TypeError:
        pass
    else:
        raise AssertionError("expected TypeError for non-string/non-date due_date")
    assert t.due_date == date.today()


def test_reschedule_invalid_date_does_not_touch_priority():
    m = TaskManager()
    t = m.add("Atomic", due_date=_iso(date.today()), priority=1)
    try:
        m.reschedule(t.id, due_date="not-a-date", priority=3)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
    assert t.priority == 1  # priority not applied because validation failed first
    assert t.due_date == date.today()


def test_reschedule_invalid_priority_does_not_touch_due_date():
    m = TaskManager()
    t = m.add("Atomic 2", due_date=_iso(date.today()), priority=1)
    new_due = date.today() + timedelta(days=5)
    try:
        m.reschedule(t.id, due_date=_iso(new_due), priority=99)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
    assert t.due_date == date.today()  # due_date not applied because validation failed
    assert t.priority == 1


# --- isolation --------------------------------------------------------------


def test_reschedule_does_not_affect_other_tasks():
    m = TaskManager()
    a = m.add("Task A", due_date=_iso(date.today() + timedelta(days=1)), priority=0)
    b = m.add("Task B", due_date=_iso(date.today() + timedelta(days=2)), priority=1)
    m.reschedule(a.id, due_date=_iso(date.today() + timedelta(days=9)), priority=3)
    assert b.due_date == date.today() + timedelta(days=2)
    assert b.priority == 1
    assert b.title == "Task B"


# --- stats / overdue interaction --------------------------------------------


def test_reschedule_out_of_overdue_decreases_overdue_count():
    m = TaskManager()
    t = m.add("Was overdue", due_date=_iso(date.today() - timedelta(days=3)))
    assert m.stats()["overdue"] == 1
    m.reschedule(t.id, due_date=_iso(date.today() + timedelta(days=3)))
    assert m.stats()["overdue"] == 0
    assert t.is_overdue() is False


def test_reschedule_into_overdue_increases_overdue_count():
    m = TaskManager()
    t = m.add("Will be overdue", due_date=_iso(date.today() + timedelta(days=3)))
    assert m.stats()["overdue"] == 0
    m.reschedule(t.id, due_date=_iso(date.today() - timedelta(days=1)))
    assert m.stats()["overdue"] == 1
    assert t.is_overdue() is True


def test_reschedule_priority_does_not_change_overdue_count():
    m = TaskManager()
    t = m.add("Priority only", due_date=_iso(date.today() - timedelta(days=1)))
    assert m.stats()["overdue"] == 1
    m.reschedule(t.id, priority=3)
    assert m.stats()["overdue"] == 1  # still overdue; priority change has no effect
