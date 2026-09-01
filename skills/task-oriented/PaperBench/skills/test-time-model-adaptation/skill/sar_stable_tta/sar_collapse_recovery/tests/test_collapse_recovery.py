from collapse_recovery import recovery_decision

def test_recovery_triggers_below_threshold():
    result = recovery_decision(0.19, 0.1, threshold=0.2)
    assert result['reset'] is True
    result2 = recovery_decision(0.5, 0.4, threshold=0.2)
    assert result2['reset'] is False
