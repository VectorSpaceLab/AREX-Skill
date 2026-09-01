from entropy_reward import particle_entropy_reward


def test_duplicate_embeddings_remain_finite_with_epsilon():
    result = particle_entropy_reward([[0, 0], [0, 0], [1, 1]], k=1, epsilon=1e-6)
    for value in result["rewards"]:
        assert value == value
        assert value != float("inf")
        assert value != float("-inf")
