from epsilon_loss import epsilon_loss, weighted_epsilon_loss


def test_exact_prediction_has_zero_loss():
    result = epsilon_loss([0.1, -0.2], [0.1, -0.2])
    assert result["mse"] == 0.0
    assert result["residuals"] == [0.0, 0.0]


def test_weighted_loss_is_positive_for_bias():
    schedule = {
        "timesteps": 2,
        "betas": [0.1, 0.2],
        "alphas": [0.9, 0.8],
        "alpha_bars": [0.9, 0.72],
        "posterior_variances": [0.0, 0.07142857142857142],
    }
    result = weighted_epsilon_loss([1.0, -1.0], [0.5, -0.5], schedule, [1, 2])
    assert result["mse"] == 0.25
    assert result["weighted_mse"] > 0.0
    assert len(result["weights"]) == 2


def test_mismatched_prediction_length_is_rejected():
    try:
        epsilon_loss([1.0, 2.0], [1.0])
    except ValueError as exc:
        assert "same length" in str(exc)
    else:
        raise AssertionError("mismatched epsilon lengths were accepted")
