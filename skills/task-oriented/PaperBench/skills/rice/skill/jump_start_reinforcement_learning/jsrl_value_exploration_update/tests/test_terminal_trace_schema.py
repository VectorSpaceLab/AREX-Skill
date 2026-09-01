from value_update import key, update_q_values


def test_terminal_transition_does_not_bootstrap_and_trace_schema_is_present():
    transitions = [{"state": 1, "action": 1, "reward": 1.0, "next_state": 2, "done": True}]
    initial = {key(2, 1): 100.0}
    updated, trace = update_q_values(initial, transitions, learning_rate=1.0, discount=0.95)
    assert updated[key(1, 1)] == 1.0
    assert "params_before" in trace
    assert "params_after" in trace
    assert trace["params_before"] != trace["params_after"]
