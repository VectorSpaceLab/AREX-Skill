from ddpm_schedule import coefficient_at, forward_sample, linear_beta_schedule


def test_schedule_products_and_monotonicity():
    schedule = linear_beta_schedule(3, 0.1, 0.3)
    assert schedule["betas"] == [0.1, 0.2, 0.3]
    assert abs(schedule["alpha_bars"][1] - 0.72) < 1e-12
    assert schedule["alpha_bar_monotone_nonincreasing"] is True
    assert coefficient_at(schedule, 2)["beta"] == 0.2


def test_forward_sample_matches_closed_form():
    schedule = linear_beta_schedule(1, 0.25, 0.25)
    value = forward_sample(schedule, 2.0, -1.0, 1)
    expected = (0.75 ** 0.5) * 2.0 + (0.25 ** 0.5) * -1.0
    assert abs(value - expected) < 1e-12


def test_invalid_beta_range_is_rejected():
    try:
        linear_beta_schedule(2, 0.2, 0.1)
    except ValueError as exc:
        assert "beta_start" in str(exc)
    else:
        raise AssertionError("invalid beta range was accepted")
