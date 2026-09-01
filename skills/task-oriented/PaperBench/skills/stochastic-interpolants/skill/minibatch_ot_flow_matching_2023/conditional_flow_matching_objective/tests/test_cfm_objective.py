from cfm_objective import build_training_batch, mean_squared_velocity_loss


def test_interpolation_and_velocity_are_linear():
    result = build_training_batch([[0, 0], [2, 2]], [[2, 4], [4, 6]], 0.5)
    assert result["x_t"] == [[1.0, 2.0], [3.0, 4.0]]
    assert result["target_velocity"] == [[2.0, 4.0], [2.0, 4.0]]


def test_perfect_prediction_has_zero_loss():
    loss = mean_squared_velocity_loss([[1, -1]], [[1, -1]])
    assert loss["loss"] == 0.0
