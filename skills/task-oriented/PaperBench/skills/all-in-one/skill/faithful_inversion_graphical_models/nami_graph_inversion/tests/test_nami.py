from nami import binary_tree_parents, moralize, nami_invert


def test_moralize_connects_coparents():
    graph = {"a": [], "b": [], "c": ["a", "b"]}
    neighbors = moralize(graph)
    assert "b" in neighbors["a"]
    assert "a" in neighbors["b"]


def test_binary_tree_topological_inverse_has_cross_subtree_parent():
    parents, latents, observed = binary_tree_parents(3)
    result = nami_invert(parents, latents, observed, mode="topological")
    assert result["elimination_order"][0] == "x0"
    assert set(result["inverse_parents"]["x0"]) == {"x1", "x2"}
    assert any(parent in result["inverse_parents"]["x2"] for parent in ["x3", "x4"])
    assert result["edge_count"] >= 9


def test_reverse_mode_keeps_observed_as_conditioning_only():
    parents, latents, observed = binary_tree_parents(3)
    result = nami_invert(parents, latents, observed, mode="reverse_topological")
    assert set(result["inverse_parents"]) == set(latents)
    assert all(variable not in observed for variable in result["inverse_parents"])
    assert any(parent in observed for values in result["inverse_parents"].values() for parent in values)


def test_depth_four_modes_are_valid_and_have_different_compactness():
    parents, latents, observed = binary_tree_parents(4)
    topological = nami_invert(parents, latents, observed, mode="topological")
    reverse = nami_invert(parents, latents, observed, mode="reverse_topological")
    assert len(topological["elimination_order"]) == len(latents)
    assert len(reverse["elimination_order"]) == len(latents)
    assert reverse["edge_count"] < topological["edge_count"]


def test_cycle_is_rejected():
    try:
        nami_invert({"a": ["b"], "b": ["a"]}, ["a"], ["b"])
    except ValueError as exc:
        assert "acyclic" in str(exc)
    else:
        raise AssertionError("cycle should be rejected")
