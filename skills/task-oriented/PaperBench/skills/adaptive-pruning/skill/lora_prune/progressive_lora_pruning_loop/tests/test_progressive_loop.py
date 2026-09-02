from progressive_loop import run_progressive_loop


def fixture():
    return {
        "x": [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
        "y": [[1.0, -1.0], [0.5, 0.25], [1.5, -0.75]],
        "W0": [[0.8, -0.8], [0.4, 0.1]],
        "B": [[0.05], [-0.02]],
        "A": [[0.1, -0.1]],
        "iterations": 4,
        "lr": 0.1,
        "target_prune_count": 1,
        "moving_average_lambda": 0.5,
    }


def test_optimizer_and_sparsity_trace():
    out = run_progressive_loop(fixture())
    assert out["optimizer_step_executed"] is True
    assert len(out["training_trace"]) == 4
    prune_counts = [r["prune_count"] for r in out["training_trace"]]
    assert prune_counts == sorted(prune_counts)
    assert prune_counts[-1] == 1
    assert "params_before" in out and "params_after" in out


def test_moving_average_recurrence_first_step():
    out = run_progressive_loop(fixture())
    first = out["training_trace"][0]
    for score, moving in zip(first["group_scores"], first["moving_average_scores"]):
        assert abs(moving - 0.5 * score) < 1e-12
