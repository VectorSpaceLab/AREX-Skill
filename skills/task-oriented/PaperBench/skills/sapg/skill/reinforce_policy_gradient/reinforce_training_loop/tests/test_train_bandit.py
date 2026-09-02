from train_bandit import sigmoid, train_bandit


def test_seeded_bandit_improves_expected_reward():
    trace = train_bandit(episodes=128, seed=7, learning_rate=0.15, baseline=0.25)
    assert trace["expected_reward_after"] > trace["expected_reward_before"]
    assert trace["params_before"] != trace["params_after"]
    assert trace["mechanism_checks"]["optimizer_step_executed"] is True


def test_probability_of_better_action_increases():
    trace = train_bandit(episodes=128, seed=7, learning_rate=0.15, baseline=0.25)
    before = sigmoid(trace["params_before"]["theta"])
    after = sigmoid(trace["params_after"]["theta"])
    assert after > before
    assert after > 0.7


def test_episode_trace_contains_score_terms():
    trace = train_bandit(episodes=8, seed=3, learning_rate=0.1, baseline=0.25)
    first = trace["episode_trace"][0]
    assert "grad_log_prob" in first
    assert "update" in first
    assert "advantage" in first


def test_baseline_flag_tracks_whether_centering_was_used():
    with_baseline = train_bandit(episodes=16, seed=5, learning_rate=0.1, baseline=0.25)
    without_baseline = train_bandit(episodes=16, seed=5, learning_rate=0.1, baseline=0.0)
    assert with_baseline["mechanism_checks"]["baseline_used"] is True
    assert without_baseline["mechanism_checks"]["baseline_used"] is False
    assert with_baseline["params_before"] != with_baseline["params_after"]
