from run_reduced_recovery import predict_grid


def test_predict_grid_shape():
    bench = {"grid": {"x": [0.0, 1.0, 2.0], "t": [0.0, 0.5]}}
    pred = predict_grid(bench, amplitude=1.0, speed=2.0)
    assert len(pred) == 2
    assert len(pred[0]) == 3
    assert pred[0][0] == 0.0
