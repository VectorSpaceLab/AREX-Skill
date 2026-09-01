from switching_rollout import ChainEnv, left_policy, right_policy, rollout_switching


def test_guide_steps_are_clamped_to_horizon():
    report = rollout_switching(ChainEnv(), right_policy, left_policy, horizon=3, guide_steps=99)
    assert report["guide_steps"] == 3
    assert all(row["controller"] == "guide" for row in report["trajectory"])


def test_zero_guide_steps_uses_only_exploration():
    report = rollout_switching(ChainEnv(), right_policy, left_policy, horizon=3, guide_steps=-5)
    assert report["guide_steps"] == 0
    assert all(row["controller"] == "exploration" for row in report["trajectory"])
