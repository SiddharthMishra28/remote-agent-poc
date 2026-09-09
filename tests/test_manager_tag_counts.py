"""Focused tests for TaskManager.tag_counts().

Covers: empty manager, single tag, repeated tags across tasks, multiple
distinct tags, tasks without tags being skipped, and combined
done+pending counting. Tags are counted exactly as stored (stripped by
``add()``; case is preserved).
"""

from tasking import TaskManager


def test_tag_counts_on_empty_manager_is_empty_dict():
    assert TaskManager().tag_counts() == {}


def test_tag_counts_single_tag():
    m = TaskManager()
    m.add("t", tags=["work"])
    assert m.tag_counts() == {"work": 1}


def test_tag_counts_repeated_tag_across_tasks():
    m = TaskManager()
    m.add("a", tags=["work"])
    m.add("b", tags=["work"])
    m.add("c", tags=["work"])
    assert m.tag_counts() == {"work": 3}


def test_tag_counts_multiple_distinct_tags():
    m = TaskManager()
    m.add("a", tags=["bug", "auth"])
    m.add("b", tags=["docs"])
    assert m.tag_counts() == {"bug": 1, "auth": 1, "docs": 1}


def test_tag_counts_task_with_several_tags_counts_each():
    m = TaskManager()
    m.add("t", tags=["bug", "auth", "urgent"])
    assert m.tag_counts() == {"bug": 1, "auth": 1, "urgent": 1}


def test_tag_counts_repeated_and_distinct_mixed():
    m = TaskManager()
    m.add("a", tags=["bug", "auth"])
    m.add("b", tags=["bug", "docs"])
    m.add("c", tags=["bug"])
    assert m.tag_counts() == {"bug": 3, "auth": 1, "docs": 1}


def test_tag_counts_skips_tasks_without_tags():
    m = TaskManager()
    m.add("no tags 1")
    m.add("no tags 2")
    m.add("tagged", tags=["work"])
    assert m.tag_counts() == {"work": 1}


def test_tag_counts_empty_tags_list_counts_nothing():
    m = TaskManager()
    m.add("explicit empty", tags=[])
    assert m.tag_counts() == {}


def test_tag_counts_combined_done_and_pending():
    m = TaskManager()
    done = m.add("done bug", tags=["bug"])
    m.add("pending bug", tags=["bug"])
    m.add("pending docs", tags=["docs"])
    m.complete(done.id)
    assert m.tag_counts() == {"bug": 2, "docs": 1}


def test_tag_counts_counts_tags_of_done_tasks_only_too():
    m = TaskManager()
    done = m.add("only", tags=["work"])
    m.complete(done.id)
    assert m.tag_counts() == {"work": 1}


def test_tag_counts_uses_stored_tags_no_mutation():
    # tags are counted exactly as stored: stripped, case preserved
    m = TaskManager()
    m.add("t1", tags=[" work "])
    m.add("t2", tags=["Work"])
    assert m.tag_counts() == {"work": 1, "Work": 1}


def test_tag_counts_reflects_removal():
    m = TaskManager()
    t = m.add("t", tags=["work"])
    m.add("keep", tags=["work"])
    m.remove(t.id)
    assert m.tag_counts() == {"work": 1}


def test_tag_counts_returns_plain_dict_of_ints():
    m = TaskManager()
    m.add("t", tags=["a", "b"])
    c = m.tag_counts()
    assert isinstance(c, dict)
    assert all(isinstance(v, int) for v in c.values())


def test_tag_counts_matches_manual_count_over_all_tasks():
    m = TaskManager()
    m.add("a", tags=["x", "y"])
    m.add("b", tags=["y"])
    m.add("c")  # no tags
    done = m.add("d", tags=["x", "z"])
    m.complete(done.id)

    manual: dict = {}
    for t in m.all():
        for tag in t.tags:
            manual[tag] = manual.get(tag, 0) + 1
    assert m.tag_counts() == manual == {"x": 2, "y": 2, "z": 1}


def test_tag_counts_readme_example():
    # mirrors the usage snippet in README.md: chore is removed before tag_counts()
    m = TaskManager()
    m.add("Fix login bug", tags=["bug", "auth"])
    m.add("Add dark mode", tags=["feature"])
    chore = m.add("Write release notes", tags=["docs"])
    done = m.add("Shipped fix", tags=["bug"])
    m.complete(done.id)
    m.remove(chore.id)
    m.add("Tag it", tags=["bug"])
    assert m.tag_counts() == {"bug": 3, "auth": 1, "feature": 1}
