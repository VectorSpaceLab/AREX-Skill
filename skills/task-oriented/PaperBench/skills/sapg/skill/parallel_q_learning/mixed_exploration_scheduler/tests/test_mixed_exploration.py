from mixed_exploration import assign_scales, noisy_actions


def test_round_robin_assignment_repeats_scales():
    assert assign_scales(8, [0.2, 0.4, 0.6, 0.8]) == [0.2, 0.4, 0.6, 0.8, 0.2, 0.4, 0.6, 0.8]


def test_noisy_actions_are_bounded_and_diverse():
    result = noisy_actions(8, [0.2, 0.4, 0.6, 0.8], 0.0, -0.5, 0.5, seed=7)
    assert min(result["actions"]) >= -0.5
    assert max(result["actions"]) <= 0.5
    assert result["stats"]["distinct_scales"] == 4
    assert result["stats"]["action_variance"] > 0.0


def test_negative_scale_is_rejected():
    try:
        assign_scales(2, [0.1, -0.2])
    except ValueError as exc:
        assert "non-negative" in str(exc)
    else:
        raise AssertionError("expected ValueError")
