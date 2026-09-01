from reward_scaling import scale_intrinsic_rewards


def test_scaled_rewards_are_finite_and_ordered():
    result = scale_intrinsic_rewards([1.0, 0.5, 0.25], gamma=0.9)
    assert result["discounted_returns"][0] > result["discounted_returns"][-1]
    assert all(value == value for value in result["scaled_rewards"])
    assert result["scaled_rewards"][0] > result["scaled_rewards"][-1]
