from probability_flow import finite_difference_divergence, gaussian_prior_logp, likelihood_summary, probability_flow_drift


def test_probability_flow_half_correction():
    drift_fn = lambda x, t: [-0.5 * item for item in x]
    diffusion_fn = lambda t: 2.0
    score_fn = lambda x, t: [-item for item in x]
    drift = probability_flow_drift([1.0], 0.5, drift_fn, diffusion_fn, score_fn)
    assert drift == [1.5]


def test_finite_difference_divergence_linear_function():
    div = finite_difference_divergence(lambda x, t: [3.0 * x[0], -2.0 * x[1]], [1.0, 2.0], 0.5)
    assert abs(div - 1.0) < 1e-8


def test_likelihood_summary_is_finite_and_has_bits_per_dim():
    result = likelihood_summary([0.0], [-0.5, -0.25], dt=0.1, data_dim=1)
    assert result["prior_logp"] < 0.0
    assert result["negative_log_likelihood"] > 0.0
    assert "bits_per_dim" in result


def test_probability_flow_divergence_matches_linear_score_fixture():
    drift_fn = lambda x, t: [0.0 for _ in x]
    diffusion_fn = lambda t: 0.5
    score_fn = lambda x, t: [-2.0 * x[0], -4.0 * x[1]]
    flow = lambda x, t: probability_flow_drift(x, t, drift_fn, diffusion_fn, score_fn)
    div = finite_difference_divergence(flow, [1.0, -1.0], 0.3)
    assert abs(div - 0.75) < 1e-8
