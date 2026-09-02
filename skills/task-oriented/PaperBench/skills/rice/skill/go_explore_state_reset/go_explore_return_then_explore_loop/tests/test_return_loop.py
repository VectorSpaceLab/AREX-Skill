from return_loop import run_go_explore_proxy, run_restart_only_baseline


def test_return_then_explore_reaches_sparse_goal():
    result = run_go_explore_proxy(iterations=12, horizon=6, seed=0)
    assert result["best"]["goal_reached"] is True
    assert result["mechanism"]["state_reset_used"] is True
    assert result["archive_size"] > 1


def test_restart_only_baseline_misses_goal():
    baseline = run_restart_only_baseline(total_steps=60)
    assert baseline["goal_reached"] is False


def test_trace_records_archive_selection_and_updates():
    result = run_go_explore_proxy(iterations=3, horizon=6, seed=0)
    first = result["trace"][0]
    assert "selected_cell" in first
    assert "restored_state" in first
    assert "archive_updates" in first
