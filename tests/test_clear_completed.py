"""Focused tests for TaskManager.clear_completed().

Covers: removing several completed tasks, mixed completed/pending,
empty manager, and that pending tasks survive with ids intact.
"""

from tasking import Task, TaskManager


def test_clear_completed_removes_several_completed_tasks():
    m = TaskManager()
    a = m.add("a")
    b = m.add("b")
    c = m.add("c")
    m.complete(a.id)
    m.complete(b.id)
    m.complete(c.id)

    removed = m.clear_completed()

    assert removed == [a, b, c]
    assert m.all() == []
    assert m.pending() == []


def test_clear_completed_removes_only_completed_in_mixed_manager():
    m = TaskManager()
    done1 = m.add("done 1")
    pending1 = m.add("pending 1")
    done2 = m.add("done 2")
    pending2 = m.add("pending 2")
    m.complete(done1.id)
    m.complete(done2.id)

    removed = m.clear_completed()

    assert removed == [done1, done2]
    assert m.all() == [pending1, pending2]
    assert m.pending() == [pending1, pending2]


def test_clear_completed_on_empty_manager_returns_empty_list():
    m = TaskManager()

    assert m.clear_completed() == []
    assert m.all() == []


def test_clear_completed_with_no_completed_tasks_mutates_nothing():
    m = TaskManager()
    a = m.add("a")
    b = m.add("b")

    before = m.all()
    removed = m.clear_completed()

    assert removed == []
    assert m.all() == before == [a, b]
    assert m.all() == [a, b]


def test_clear_completed_pending_tasks_survive_with_ids_intact():
    m = TaskManager()
    m.add("completed and gone")
    keeper1 = m.add("keeper 1")
    m.add("also completed and gone")
    keeper2 = m.add("keeper 2")
    for t in m.all():
        if t.title.startswith("completed") or t.title.startswith("also"):
            m.complete(t.id)

    removed = m.clear_completed()

    assert [t.id for t in m.pending()] == [keeper1.id, keeper2.id]
    assert [t.id for t in m.all()] == [keeper1.id, keeper2.id]
    assert all(t.done is False for t in m.all())
    assert len(removed) == 2
    assert all(t.done is True for t in removed)


def test_clear_completed_returns_task_objects_in_insertion_order():
    m = TaskManager()
    first = m.add("first")
    second = m.add("second")
    third = m.add("third")
    m.complete(third.id)   # completed out of insertion order
    m.complete(first.id)
    m.complete(second.id)

    removed = m.clear_completed()

    assert removed == [first, second, third]
    assert all(isinstance(t, Task) for t in removed)


def test_clear_completed_is_idempotent():
    m = TaskManager()
    t = m.add("t")
    m.complete(t.id)

    assert m.clear_completed() == [t]
    assert m.clear_completed() == []
    assert m.all() == []


def test_clear_completed_does_not_reset_id_counter():
    m = TaskManager()
    a = m.add("a")
    m.complete(a.id)
    m.clear_completed()

    b = m.add("b")
    assert b.id == a.id + 1


def test_clear_completed_removed_tasks_are_really_gone():
    m = TaskManager()
    t = m.add("t")
    m.complete(t.id)
    m.clear_completed()

    assert m.all() == []
    assert m.search("t") == []
    assert m.by_priority(0) == []
