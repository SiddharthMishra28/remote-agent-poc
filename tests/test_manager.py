from tasking import TaskManager, TaskNotFoundError


def test_add_and_complete():
    m = TaskManager()
    t = m.add("write docs")
    assert m.complete(t.id).done


def test_pending():
    m = TaskManager()
    m.add("one"); m.add("two")
    assert len(m.pending()) == 2
