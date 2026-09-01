from bar_optimizer import train_zo, toy_black_box


def test_q1_stress_keeps_executable_query_only_loop():
    features = [[0.9,0.1,0.0,0.0], [0.1,0.9,0.0,0.0]]
    labels = [1, 0]
    out = train_zo(features, labels, [0.0,0.0,1.0,1.0], {0:[0,1],1:[2,3]}, toy_black_box, iterations=1, q=1, seed=11)
    assert out["query_count"] >= 6
    assert out["params_before"] != out["params_after"]
