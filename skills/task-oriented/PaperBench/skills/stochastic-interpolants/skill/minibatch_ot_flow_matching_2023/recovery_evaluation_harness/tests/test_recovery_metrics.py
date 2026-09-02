from recovery_math import gradient_for_scalar_weight, linear_predictions, mse


def test_scalar_update_reduces_simple_loss():
    points = [[1.0], [2.0]]
    targets = [[2.0], [4.0]]
    weight = 0.0
    before = mse(linear_predictions(points, weight), targets)
    grad = gradient_for_scalar_weight(points, targets, weight)
    after_weight = weight - 0.1 * grad
    after = mse(linear_predictions(points, after_weight), targets)
    assert after < before
