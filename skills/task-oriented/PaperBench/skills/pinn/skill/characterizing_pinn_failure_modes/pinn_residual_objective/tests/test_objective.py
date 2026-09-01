from objective import loss_decomposition


def tiny_benchmark():
    return {
        "coefficients": {"beta": 5.0},
        "initial_condition": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.8414709848]],
        "boundary_pairs": [[[0.0, 0.0], [6.283185307179586, 0.0]], [[0.0, 1.0], [6.283185307179586, 1.0]]],
        "collocation": [[0.1, 0.2], [1.0, 0.5], [2.0, 0.7]]
    }


def test_residual_sensitive_to_speed_mismatch():
    bench = tiny_benchmark()
    matched = loss_decomposition(bench, amplitude=1.0, speed=5.0, beta=5.0)
    mismatched = loss_decomposition(bench, amplitude=1.0, speed=1.0, beta=5.0)
    assert matched["residual_loss"] < 1e-20
    assert mismatched["residual_loss"] > matched["residual_loss"]
    assert mismatched["total_loss"] > matched["total_loss"]
