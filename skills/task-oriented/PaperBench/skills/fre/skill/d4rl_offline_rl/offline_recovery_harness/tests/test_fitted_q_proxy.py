from fitted_q_proxy import one_gradient_step


def test_one_gradient_step_changes_params_and_reduces_loss():
    transitions = [
        {"observation": [0], "action": 0, "reward": 1.0, "next_observation": [1], "terminal": False, "timeout": False},
        {"observation": [1], "action": 0, "reward": 1.0, "next_observation": [2], "terminal": True, "timeout": False},
    ]
    trace = one_gradient_step(transitions, weight=0.0, learning_rate=0.05)
    assert trace["params_before"] != trace["params_after"]
    assert trace["loss_after"] < trace["loss_before"]
    assert trace["optimizer_state_changed"] is True
