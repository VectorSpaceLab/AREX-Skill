from advantage import compute_gae


def test_terminal_reset_and_returns():
    result = compute_gae([
        {"reward": 1.0, "value": 0.5, "done": False},
        {"reward": 2.0, "value": 0.25, "done": True},
    ], last_value=10.0, gamma=1.0, gae_lambda=1.0)
    assert result["deltas"] == [0.75, 1.75]
    assert result["advantages"] == [2.5, 1.75]
    assert result["returns"] == [3.0, 2.0]
    assert result["diagnostics"]["terminal_resets"] == 1


def test_rejects_empty_rollout():
    try:
        compute_gae([], last_value=0.0)
    except ValueError as exc:
        assert "rollout" in str(exc)
    else:
        raise AssertionError("empty rollout should fail")
