"""Focused tests for TaskManager.complete_all().

Covers: empty manager, all-done manager, mixed manager (only pending
tasks completed and returned, in insertion order), done flags afterwards,
and stats() reflecting the new state.
"""

from tasking import Task, TaskManager


def test_complete_all_on_empty_manager_returns_empty_list():
    m = TaskManager()

    assert m.complete_all() == []
    assert m.all() == []


def test_complete_all_on_all_done_manager_returns_empty_list():
    m = TaskManager()
    a = m.add("a")
    b = m.add("b")
    m.complete(a.id)
    m.complete(b.id)

    assert m.complete_all() == []
    assert m.all() == [a, b]
    assert all(t.done is True for t in m.all())


def test_complete_all_completes_only_pending_and_returns_exactly_them():
    m = TaskManager()
    done1 = m.add("done 1")
    pending1 = m.add("pending 1")
    done2 = m.add("done 2")
    pending2 = m.add("pending 2")
    m.complete(done1.id)
    m.complete(done2.id)

    completed = m.complete_all()

    assert completed == [pending1, pending2]
    assert m.pending() == []
    assert m.all() == [done1, pending1, done2, pending2]


def test_complete_all_returns_tasks_in_insertion_order():
    m = TaskManager()
    first = m.add("first")
    second = m.add("second")
    third = m.add("third")
    m.complete(second.id)  # complete out of insertion order first

    completed = m.complete_all()

    assert completed == [first, third]
    assert all(isinstance(t, Task) for t in completed)


def test_completed_tasks_report_done_true_afterwards():
    m = TaskManager()
    a = m.add("a")
    b = m.add("b")

    m.complete_all()

    assert a.done is True
    assert b.done is True
    assert all(t.done is True for t in m.all())


def test_complete_all_returns_the_same_task_objects():
    m = TaskManager()
    a = m.add("a")
    b = m.add("b")

    completed = m.complete_all()

    assert completed[0] is a
    assert completed[1] is b


def test_stats_reflect_all_completed_after_complete_all():
    m = TaskManager()
    m.add("a")
    m.add("b")
    m.add("c")
    m.complete(m.all()[0].id)

    m.complete_all()

    assert m.stats() == {"total": 3, "pending": 0, "completed": 3, "overdue": 0}


def test_complete_all_is_idempotent():
    m = TaskManager()
    t = m.add("t")

    assert m.complete_all() == [t]
    assert m.complete_all() == []
    assert m.all() == [t]
    assert t.done is True


def test_complete_all_does_not_remove_tasks_or_reset_ids():
    m = TaskManager()
    a = m.add("a")
    m.complete_all()

    b = m.add("b")
    assert b.id == a.id + 1
    assert m.all() == [a, b]
