"""Focused tests for TaskManager.due_soon(): window semantics, exclusions and ordering."""

from datetime import date, timedelta

from tasking import TaskManager


def _iso(d):
    """Format a date as the ISO string accepted by TaskManager.add()."""
    return d.isoformat()


# --- window basics ---------------------------------------------------------


def test_due_soon_on_empty_manager_returns_empty_list():
    m = TaskManager()
    assert m.due_soon() == []


def test_task_due_well_inside_window_is_included():
    m = TaskManager()
    m.add("Deploy hotfix", due_date=_iso(date.today() + timedelta(days=1)))
    result = m.due_soon()
    assert [t.title for t in result] == ["Deploy hotfix"]


def test_task_due_well_beyond_window_is_excluded():
    m = TaskManager()
    m.add("Plan conference", due_date=_iso(date.today() + timedelta(days=30)))
    assert m.due_soon() == []


def test_task_due_today_is_included():
    m = TaskManager()
    m.add("File taxes", due_date=_iso(date.today()))
    assert [t.title for t in m.due_soon()] == ["File taxes"]


def test_boundary_due_in_exactly_48_hours_is_included():
    m = TaskManager()
    m.add("Boundary task", due_date=_iso(date.today() + timedelta(hours=48)))
    assert [t.title for t in m.due_soon()] == ["Boundary task"]


# --- exclusions ------------------------------------------------------------


def test_done_tasks_are_excluded():
    m = TaskManager()
    m.add("Done soon task", due_date=_iso(date.today() + timedelta(days=1)))
    m.complete(1)
    assert m.due_soon() == []


def test_tasks_without_due_date_are_excluded():
    m = TaskManager()
    m.add("No deadline task")
    assert m.due_soon() == []


def test_overdue_task_is_excluded():
    m = TaskManager()
    m.add("Overdue task", due_date=_iso(date.today() - timedelta(days=1)))
    assert m.due_soon() == []


# --- ordering --------------------------------------------------------------


def test_results_sorted_by_due_date_ascending():
    m = TaskManager()
    m.add("Later", due_date=_iso(date.today() + timedelta(days=2)))
    m.add("Sooner", due_date=_iso(date.today() + timedelta(days=1)))
    m.add("Soonest", due_date=_iso(date.today()))
    assert [t.title for t in m.due_soon()] == ["Soonest", "Sooner", "Later"]


def test_same_date_tasks_keep_insertion_order():
    m = TaskManager()
    m.add("First", due_date=_iso(date.today() + timedelta(days=1)))
    m.add("Second", due_date=_iso(date.today() + timedelta(days=1)))
    assert [t.title for t in m.due_soon()] == ["First", "Second"]


# --- custom windows --------------------------------------------------------


def test_custom_hours_widens_the_window():
    m = TaskManager()
    m.add("Next week task", due_date=_iso(date.today() + timedelta(days=5)))
    assert m.due_soon() == []
    assert [t.title for t in m.due_soon(hours=24 * 7)] == ["Next week task"]


def test_custom_hours_zero_only_includes_tasks_due_today():
    m = TaskManager()
    m.add("Today task", due_date=_iso(date.today()))
    m.add("Tomorrow task", due_date=_iso(date.today() + timedelta(days=1)))
    assert [t.title for t in m.due_soon(hours=0)] == ["Today task"]


# --- mixed inputs and consistency ------------------------------------------


def test_date_objects_and_iso_strings_are_both_supported():
    m = TaskManager()
    m.add("ISO task", due_date=_iso(date.today() + timedelta(days=1)))
    m.add("Date object task", due_date=date.today() + timedelta(days=2))
    assert [t.title for t in m.due_soon()] == ["ISO task", "Date object task"]


def test_due_soon_agrees_with_pending_and_manual_filter():
    m = TaskManager()
    m.add("Inside", due_date=_iso(date.today() + timedelta(days=1)))
    m.add("Outside", due_date=_iso(date.today() + timedelta(days=10)))
    m.add("Overdue", due_date=_iso(date.today() - timedelta(days=2)))
    m.add("No date")
    deadline = date.today() + timedelta(hours=48)
    expected = [
        t
        for t in m.pending()
        if t.due_date is not None and date.today() <= t.due_date <= deadline
    ]
    assert m.due_soon() == expected


# --- argument validation ---------------------------------------------------


def test_due_soon_rejects_non_numeric_hours():
    m = TaskManager()
    try:
        m.due_soon(hours="2")
    except TypeError:
        pass
    else:
        raise AssertionError("expected TypeError for string hours")


def test_due_soon_rejects_negative_hours():
    m = TaskManager()
    try:
        m.due_soon(hours=-1)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for negative hours")
