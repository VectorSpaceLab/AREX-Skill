from policy_update import policy_update_step


def test_policy_update_changes_params_and_improves_loss():
    result = policy_update_step([0.0, 0.0, 0.0], [-1.0, 0.0, 1.0], learning_rate=0.3, entropy_coef=0.01)
    assert result["optimizer_step_executed"] is True
    assert result["params_before"] != result["params_after"]
    assert result["loss_after"] <= result["loss_before"]
    assert result["loss_delta"] >= 0.0
