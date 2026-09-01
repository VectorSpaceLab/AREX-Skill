from protocol import validate_unroll

def test_validate_unroll_detects_lag():
    out=validate_unroll({"rewards":[1,0],"discounts":[0.9,0.9],"actions":[0,1],"values":[0.2,0.1,0.0],"target_policy":[[0.8,0.2],[0.4,0.6]],"behavior_policy":[[0.5,0.5],[0.7,0.3]]})
    assert out["has_policy_lag"] is True
    assert out["target_action_probs"] == [0.8,0.6]

def test_rejects_bad_bootstrap_length():
    try:
        validate_unroll({"rewards":[1],"discounts":[0.9],"actions":[0],"values":[0.2],"target_policy":[[1.0]],"behavior_policy":[[1.0]]})
    except ValueError as exc:
        assert "bootstrap" in str(exc)
    else:
        raise AssertionError("expected error")

def test_rejects_zero_behavior_action_probability():
    try:
        validate_unroll({"rewards":[1.0],"discounts":[0.9],"actions":[0],"values":[0.0,0.0],"target_policy":[[1.0,0.0]],"behavior_policy":[[0.0,1.0]]})
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("expected zero-probability behavior action to fail")
