import math

from apt_transform import gaussian_transform_1d, normal_log_prob, normalize_transformed_scores


def test_gaussian_transform_has_positive_variance_for_narrow_proposal():
    result = gaussian_transform_1d(
        prior_mean=0.0,
        prior_variance=4.0,
        proposal_mean=0.5,
        proposal_variance=0.5,
        posterior_mean=0.6,
        posterior_variance=0.4,
    )
    assert result["ok"]
    assert result["variance"] > 0.0
    assert result["variance"] < 0.4


def test_finite_normalization_is_constant_shift_invariant():
    log_q = [-1.0, -0.5, -2.0]
    log_proposal = [-0.2, -0.2, -0.2]
    log_prior = [-1.2, -1.2, -1.2]
    base = normalize_transformed_scores(log_q, log_proposal, log_prior)["probabilities"]
    shifted = normalize_transformed_scores([value + 10.0 for value in log_q], log_proposal, log_prior)["probabilities"]
    assert all(abs(a - b) < 1e-12 for a, b in zip(base, shifted))
    assert abs(sum(base) - 1.0) < 1e-12


def test_gaussian_transform_matches_grid_mode():
    result = gaussian_transform_1d(0.0, 4.0, 0.7, 0.3, 0.5, 0.4)
    assert result["ok"]
    grid = [-0.5 + i * 0.01 for i in range(201)]
    scores = normalize_transformed_scores(
        [normal_log_prob(v, 0.5, 0.4) for v in grid],
        [normal_log_prob(v, 0.7, 0.3) for v in grid],
        [normal_log_prob(v, 0.0, 4.0) for v in grid],
    )
    grid_mean = sum(v * p for v, p in zip(grid, scores["probabilities"]))
    assert math.isfinite(grid_mean)
    assert abs(grid_mean - result["mean"]) < 0.08


def test_invalid_gaussian_precision_is_reported():
    result = gaussian_transform_1d(
        prior_mean=0.0,
        prior_variance=0.1,
        proposal_mean=0.0,
        proposal_variance=10.0,
        posterior_mean=0.0,
        posterior_variance=10.0,
    )
    assert result["ok"] is False
    assert result["transformed_precision"] <= 0.0
