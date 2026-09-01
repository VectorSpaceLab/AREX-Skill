from archive import select_cell, update_archive


def test_archive_inserts_new_cell():
    archive = {}
    changed = update_archive(archive, {"cell_key": (0, 0), "state": {}, "actions": [], "score": 0})
    assert changed is True
    assert (0, 0) in archive


def test_archive_replaces_higher_score():
    archive = {}
    update_archive(archive, {"cell_key": (1,), "state": {}, "actions": ["a"], "score": 1})
    changed = update_archive(archive, {"cell_key": (1,), "state": {}, "actions": ["b", "c"], "score": 2})
    assert changed is True
    assert archive[(1,)]["score"] == 2


def test_archive_replaces_shorter_equal_score():
    archive = {}
    update_archive(archive, {"cell_key": (1,), "state": {}, "actions": ["a", "b"], "score": 2})
    changed = update_archive(archive, {"cell_key": (1,), "state": {}, "actions": ["c"], "score": 2})
    assert changed is True
    assert archive[(1,)]["actions"] == ["c"]


def test_archive_rejects_lower_score():
    archive = {}
    update_archive(archive, {"cell_key": (1,), "state": {}, "actions": ["a"], "score": 3})
    changed = update_archive(archive, {"cell_key": (1,), "state": {}, "actions": [], "score": 2})
    assert changed is False
    assert archive[(1,)]["score"] == 3


def test_selection_is_seeded_and_counts():
    archive = {}
    update_archive(archive, {"cell_key": (0,), "state": {}, "actions": [], "score": 0})
    key, entry = select_cell(archive, seed=5)
    assert key == (0,)
    assert entry["selection_count"] == 1
