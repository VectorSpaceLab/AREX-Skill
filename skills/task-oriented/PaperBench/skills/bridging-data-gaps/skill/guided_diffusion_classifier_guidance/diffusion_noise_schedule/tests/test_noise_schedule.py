from noise_schedule import build_schedule


def test_linear_schedule_is_valid():
    result = build_schedule("linear", 8)
    assert result["valid"] is True
    assert len(result["betas"]) == 8
    assert all(0 < beta <= 1 for beta in result["betas"])


def test_cosine_schedule_decreases_alpha_cumprod():
    result = build_schedule("cosine", 6)
    values = result["alphas_cumprod"]
    assert all(later < earlier for earlier, later in zip(values, values[1:]))
    assert len(result["posterior_mean_coef1"]) == 6
