from progressive_loop import run_progressive_loop


def test_zero_target_prune_keeps_all_groups():
    data = {
        "x": [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
        "y": [[1.0, -1.0], [0.5, 0.25], [1.5, -0.75]],
        "W0": [[0.8, -0.8], [0.4, 0.1]],
        "B": [[0.05], [-0.02]],
        "A": [[0.1, -0.1]],
        "iterations": 4,
        "lr": 0.1,
        "target_prune_count": 0,
        "moving_average_lambda": 0.5,
    }
    out = run_progressive_loop(data)
    assert out["final_group_mask"] == [1, 1]
    assert all(step["prune_count"] == 0 for step in out["training_trace"])
