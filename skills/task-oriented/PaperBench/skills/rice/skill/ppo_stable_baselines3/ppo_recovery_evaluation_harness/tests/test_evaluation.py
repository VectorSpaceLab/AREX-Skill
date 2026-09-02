from evaluate_recovery import evaluate_recovery_evidence


def test_complete_mechanism_passes():
    trace = {
        "params_before": {"x": 0.0},
        "params_after": {"x": 1.0},
        "mechanism_checks": {
            "gae_executed": True,
            "clipped_surrogate_executed": True,
            "value_loss_executed": True,
            "optimizer_step_executed": True,
        },
    }
    result = evaluate_recovery_evidence(trace, {"forbidden_sources_detected": []}, True)
    assert result["passed"] is True
    assert result["mechanism_pass_rate"] == 1.0


def test_missing_optimizer_fails():
    trace = {
        "params_before": {"x": 0.0},
        "params_after": {"x": 0.0},
        "mechanism_checks": {"gae_executed": True, "clipped_surrogate_executed": True, "value_loss_executed": True},
    }
    result = evaluate_recovery_evidence(trace, {"forbidden_sources_detected": []}, True)
    assert result["passed"] is False
    assert "optimizer_step_executed" in result["missing"]
