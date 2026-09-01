from value_update import demo_transitions, greedy_action, key, update_q_values


def test_q_update_changes_reward_action_value():
    updated, trace = update_q_values({}, demo_transitions(), learning_rate=0.5)
    assert trace["optimizer_state_changed"] is True
    assert updated[key(5, 1)] > 0.0
    assert trace["params_before"] != trace["params_after"]


def test_greedy_action_prefers_higher_value():
    params = {key(0, -1): 0.1, key(0, 1): 0.5}
    assert greedy_action(params, 0) == 1
