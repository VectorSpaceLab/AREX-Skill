import math

from score_training import denoising_target, train_one_step


def test_denoising_target_is_finite():
    theta = [[1.0, -1.0]]
    noisy = [[0.5, -0.25]]
    target = denoising_target(theta, noisy, 0.5)
    assert len(target) == 1
    assert len(target[0]) == 2
    assert all(math.isfinite(value) for row in target for value in row)


def test_train_one_step_changes_parameters_and_keeps_loss_finite():
    theta = [[0.2, -0.1], [0.4, 0.3], [-0.2, 0.5], [0.1, -0.4]]
    condition = [[value + 0.1 for value in row] for row in theta]
    trace = train_one_step(theta, condition, gamma=0.7, learning_rate=0.02, seed=3)
    assert trace["optimizer_state_changed"] is True
    assert trace["loss_before"] >= 0.0
    assert trace["loss_after"] >= 0.0
    assert len(trace["params_before"]) == len(trace["params_after"])
    assert trace["params_before"] != trace["params_after"]
