from reverse_step import reverse_mean, reverse_sample


def test_reverse_mean_matches_formula():
    schedule = {"timesteps": 1, "betas": [0.25], "alphas": [0.75], "alpha_bars": [0.75], "posterior_variances": [0.0]}
    value = reverse_mean(schedule, 1.0, 0.5, 1)
    expected = (1.0 - 0.25 * 0.5 / (1.0 - 0.75) ** 0.5) / (0.75 ** 0.5)
    assert abs(value - expected) < 1e-12


def test_zero_variance_sample_returns_mean():
    schedule = {"timesteps": 1, "betas": [0.25], "alphas": [0.75], "alpha_bars": [0.75], "posterior_variances": [0.0]}
    result = reverse_sample(schedule, [1.0, 2.0], [0.1, -0.1], 1, z=0.0, variance_mode="zero")
    assert result["sample"] == result["mean"]
    assert result["sigma"] == 0.0


def test_out_of_range_timestep_is_rejected():
    schedule = {"timesteps": 1, "betas": [0.25], "alphas": [0.75], "alpha_bars": [0.75], "posterior_variances": [0.0]}
    try:
        reverse_mean(schedule, 1.0, 0.0, 2)
    except ValueError as exc:
        assert "out of range" in str(exc)
    else:
        raise AssertionError("out-of-range timestep was accepted")
