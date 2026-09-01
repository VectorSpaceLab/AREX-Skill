from bar_optimizer import train_zo, toy_black_box


def test_zeroth_order_training_changes_params_and_logs_queries():
    features = [[0.8, 0.1, 0.0, 0.0], [0.7, 0.2, 0.0, 0.0], [0.1, 0.8, 0.0, 0.0], [0.2, 0.7, 0.0, 0.0]]
    labels = [1, 1, 0, 0]
    mask = [0.0, 0.0, 1.0, 1.0]
    mapping = {0: [0, 1], 1: [2, 3]}
    out = train_zo(features, labels, mask, mapping, toy_black_box, iterations=3, q=2, seed=3)
    assert out["query_count"] > 0
    assert out["params_before"] != out["params_after"]
    assert len(out["trace"]) == 3
    assert isinstance(out["loss_after"], float)
