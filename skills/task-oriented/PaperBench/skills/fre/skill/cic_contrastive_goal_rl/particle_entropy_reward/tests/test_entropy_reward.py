from entropy_reward import particle_entropy_reward


def test_rewards_are_finite():
    result = particle_entropy_reward([[0, 0], [0.1, 0], [2, 2]], k=1)
    assert len(result["rewards"]) == 3
    assert result["diagnostics"]["effective_k"] == 1
    assert all(value == value for value in result["rewards"])


def test_isolated_point_has_higher_reward_than_cluster_point():
    result = particle_entropy_reward([[0, 0], [0.01, 0], [5, 5]], k=1)
    assert result["rewards"][2] > result["rewards"][0]


def test_rejects_single_embedding():
    try:
        particle_entropy_reward([[0, 0]])
    except ValueError as exc:
        assert "at least two" in str(exc)
    else:
        raise AssertionError("expected ValueError")
