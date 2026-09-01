from gaussian_score_training import build_training_trace, exact_score, single_observation_posterior


def test_gaussian_score_points_toward_posterior_mean():
    mean, variance = single_observation_posterior(1.0)
    assert variance > 0
    assert exact_score(mean + 0.2, 1.0) < 0
    assert exact_score(mean - 0.2, 1.0) > 0


def test_gradient_step_changes_params_and_loss_is_finite():
    trace = build_training_trace([0.2, 0.8], [-1.0, 0.0, 1.0], learning_rate=0.01)
    assert trace["params_before"] != trace["params_after"]
    assert trace["loss_after"] >= 0
    assert trace["loss_after"] < trace["loss_before"]
    assert trace["reduced_training_executed"] is True
