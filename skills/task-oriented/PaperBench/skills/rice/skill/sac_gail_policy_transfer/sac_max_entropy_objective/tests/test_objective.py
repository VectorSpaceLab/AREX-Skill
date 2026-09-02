from entropy_objective import compute_entropy_objective

def test_soft_value_and_actor_loss():
    result = compute_entropy_objective([2.0, 1.0], [-0.5, -1.0], alpha=0.2)
    assert result['soft_values'] == [2.1, 1.2]
    assert result['actor_losses'] == [-2.1, -1.2]
    assert abs(result['mean_soft_value'] - 1.65) < 1e-9
