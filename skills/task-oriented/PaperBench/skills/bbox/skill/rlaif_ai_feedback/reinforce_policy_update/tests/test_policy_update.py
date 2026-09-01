from policy_update import reinforce_step, softmax


def test_positive_reward_increases_chosen_action_probability():
    result = reinforce_step([0.0, 0.0], 1, 1.0, baseline=0.0, learning_rate=0.5)
    assert result["probabilities_after"][1] > result["probabilities_before"][1]
    assert result["loss_after"] < result["loss_before"]


def test_trace_has_validator_parameter_fields_and_change():
    result = reinforce_step([0.2, -0.1], 0, 0.5)
    assert "params_before" in result
    assert "params_after" in result
    assert result["params_before"] != result["params_after"]
    assert result["optimizer_state_changed"] is True


def test_softmax_normalized():
    probs = softmax([1.0, 2.0, 3.0])
    assert abs(sum(probs) - 1.0) < 1e-9
    assert probs[2] > probs[1] > probs[0]
