from kd_objective import total_objective, validate_lambdas


def test_weighted_total_exact():
    result = total_objective(0.4, 0.3, 0.2, [0.2, 0.3, 0.5])
    assert abs(result["total_loss"] - 0.27) < 1e-12
    assert result["contributions"]["rail"] == 0.1
    assert result["weights_sum_to_one"] is True


def test_invalid_lambda_sum_raises():
    try:
        validate_lambdas([0.2, 0.2, 0.2])
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_negative_loss_raises():
    try:
        total_objective(-0.1, 0.2, 0.3, [0.2, 0.3, 0.5])
        assert False, "expected ValueError"
    except ValueError:
        pass
