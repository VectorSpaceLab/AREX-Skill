from lexi_target_formulation import compute_historical_targets


def test_nested_frontier_with_tolerance():
    result = compute_historical_targets([[0.10, 10], [0.12, 2], [0.20, 1]], [None, None], [0.03, 0.0])
    assert result["targets"] == [0.13, 2.0]
    assert result["frontiers"] == [[0, 1], [1]]
    assert result["best_index"] == 1


def test_goal_overrides_lower_priority_target():
    result = compute_historical_targets([[0.10, 600], [0.13, 500], [0.11, 300]], [None, 500], [0.05, 0.0])
    assert result["targets"][1] == 500.0
    assert result["frontiers"][-1] == [1, 2]
