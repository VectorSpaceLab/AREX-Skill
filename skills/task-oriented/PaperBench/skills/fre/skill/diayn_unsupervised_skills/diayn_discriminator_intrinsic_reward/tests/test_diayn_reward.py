import math

from diayn_reward import compute_diayn_rewards


def test_confident_correct_logits_have_high_reward_and_accuracy():
    log_prior = -math.log(3)
    confident = compute_diayn_rewards([[4.0, 0.0, 0.0], [0.0, 4.0, 0.0]], [0, 1], log_prior)
    confused = compute_diayn_rewards([[0.0, 4.0, 0.0], [4.0, 0.0, 0.0]], [0, 1], log_prior)
    assert confident["accuracy"] == 1.0
    assert confused["accuracy"] == 0.0
    assert confident["mean_reward"] > confused["mean_reward"]
    assert confident["cross_entropy_loss"] < confused["cross_entropy_loss"]
