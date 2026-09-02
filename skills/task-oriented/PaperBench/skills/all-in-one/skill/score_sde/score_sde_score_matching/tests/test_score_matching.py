from score_matching import LinearScoreModel, build_score_matching_batch, optimizer_step, score_matching_loss


def test_batch_builds_conditional_score_targets():
    marginal = lambda x0, t: (2.0 * x0, 0.5)
    batch = build_score_matching_batch([1.0], [0.3], [0.25], marginal)
    assert batch.perturbed == [2.125]
    assert batch.target == [-0.5]


def test_likelihood_weighting_uses_diffusion_square():
    marginal = lambda x0, t: (x0, 1.0)
    batch = build_score_matching_batch([0.0], [0.4], [1.0], marginal)
    raw = score_matching_loss([0.0], batch)["loss"]
    weighted = score_matching_loss([0.0], batch, likelihood_weighting=True, diffusion_sq_fn=lambda t: 3.0)["loss"]
    assert raw == 1.0
    assert weighted == 3.0


def test_optimizer_step_changes_params_and_reduces_loss():
    marginal = lambda x0, t: (0.8 * x0, 0.5 + 0.1 * t)
    batch = build_score_matching_batch([1.0, -1.0, 0.5], [0.2, 0.4, 0.6], [0.5, -0.25, 0.1], marginal)
    trace = optimizer_step(LinearScoreModel(weight=-0.1), batch, learning_rate=0.05)
    assert trace["params_before"] != trace["params_after"]
    assert trace["loss_after"] < trace["loss_before"]


def test_likelihood_weighted_optimizer_step_reduces_weighted_loss():
    marginal = lambda x0, t: (0.9 * x0, 0.4 + 0.2 * t)
    batch = build_score_matching_batch([1.0, -0.5, 0.25], [0.2, 0.5, 0.8], [0.3, -0.4, 0.2], marginal)
    trace = optimizer_step(
        LinearScoreModel(weight=-0.05, time_weight=0.02),
        batch,
        learning_rate=0.02,
        likelihood_weighting=True,
        diffusion_sq_fn=lambda t: 0.1 + t,
    )
    assert trace["params_before"] != trace["params_after"]
    assert trace["loss_after"] < trace["loss_before"]
