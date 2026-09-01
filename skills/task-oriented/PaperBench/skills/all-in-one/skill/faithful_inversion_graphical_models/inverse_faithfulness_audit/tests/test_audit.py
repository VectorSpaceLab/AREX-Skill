from audit_inverse import audit_inverse, d_separated


def test_d_separation_fork_and_collider():
    fork = {"a": [], "b": ["a"], "c": ["a"]}
    assert not d_separated(fork, "b", "c", [])
    assert d_separated(fork, "b", "c", ["a"])
    collider = {"a": [], "b": [], "c": ["a", "b"]}
    assert d_separated(collider, "a", "b", [])
    assert not d_separated(collider, "a", "b", ["c"])


def test_unfaithful_fork_inverse_fails_local_imap():
    parents = {"a": [], "b": ["a"], "c": ["a"]}
    inverse = {"a": ["b", "c"], "b": [], "c": []}
    report = audit_inverse(parents, inverse, ["a", "b", "c"], [], mode="topological")
    assert not report["ok"]
    assert not report["local_imap_ok"]


def test_partially_reversed_fork_inverse_reports_missing_sibling_parent():
    parents = {"a": [], "b": ["a"], "c": ["a"]}
    inverse = {"a": ["b"], "b": [], "c": []}
    report = audit_inverse(parents, inverse, ["a", "b", "c"], [], mode="topological")
    assert not report["local_imap_ok"]
    assert any(item.get("variable") == "a" and item.get("other") == "c" for item in report["issues"])


def test_nami_style_binary_tree_inverse_passes():
    parents = {
        "x0": [],
        "x1": ["x0"],
        "x2": ["x0"],
        "x3": ["x1"],
        "x4": ["x1"],
        "x5": ["x2"],
        "x6": ["x2"],
    }
    inverse = {
        "x0": ["x1", "x2"],
        "x1": ["x2", "x3", "x4"],
        "x2": ["x3", "x4", "x5", "x6"],
    }
    report = audit_inverse(parents, inverse, ["x0", "x1", "x2"], ["x3", "x4", "x5", "x6"], mode="topological")
    assert report["ok"], report["issues"]
    assert report["checked_edges"] == 9
