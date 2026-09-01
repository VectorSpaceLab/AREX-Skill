from score_estimator import bernoulli_score_update


def test_high_reward_action_one_has_positive_update():
    result = bernoulli_score_update(0.25, 1, 1.0, 0.0)
    assert result["grad_log_prob"] > 0
    assert result["update"] > 0


def test_low_reward_action_zero_against_positive_baseline_increases_action_one():
    result = bernoulli_score_update(0.7, 0, 0.0, 0.5)
    assert result["grad_log_prob"] < 0
    assert result["advantage"] < 0
    assert result["update"] > 0


def test_action_independent_baseline_preserves_sign_for_good_action():
    no_baseline = bernoulli_score_update(0.4, 1, 1.0, 0.0)
    with_baseline = bernoulli_score_update(0.4, 1, 1.0, 0.2)
    assert no_baseline["update"] > 0
    assert with_baseline["update"] > 0
    assert with_baseline["update"] < no_baseline["update"]


def test_probability_inputs_are_clamped_for_numerical_safety():
    result = bernoulli_score_update(0.0, 1, 1.0, 0.0)
    assert 0.0 < result["prob_action_one"] < 1.0
    assert result["update"] > 0.99
