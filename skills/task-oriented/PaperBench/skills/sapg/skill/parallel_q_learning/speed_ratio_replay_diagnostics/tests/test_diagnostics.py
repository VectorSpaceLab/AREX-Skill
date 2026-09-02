from diagnostics import compute_diagnostics


def test_high_parallelism_flags_replay_overwrite():
    result = compute_diagnostics(10000, 1, 1000000, 10000, 1, 100)
    assert result["replay_refresh_ticks"] == 100
    assert "high_replay_overwrite_pressure" in result["warnings"]
    assert "actor_throughput_may_outpace_value_learning" in result["warnings"]


def test_balanced_configuration_has_no_overwrite_warning():
    result = compute_diagnostics(64, 1, 1000000, 64, 64, 64)
    assert result["replay_refresh_ticks"] > 100
    assert "high_replay_overwrite_pressure" not in result["warnings"]


def test_zero_rate_is_rejected():
    try:
        compute_diagnostics(64, 1, 1000, 1, 1, 0)
    except ValueError as exc:
        assert "value_rate" in str(exc)
    else:
        raise AssertionError("expected ValueError")
