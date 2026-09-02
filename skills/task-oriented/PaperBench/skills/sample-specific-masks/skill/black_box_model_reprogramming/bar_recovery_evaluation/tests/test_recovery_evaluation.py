from evaluate_bar_recovery import accuracy, build_mechanism_checks, build_recovery_result


def test_accuracy_and_mechanism_checks_require_changed_params():
    trace = {"params_before": [0.0], "params_after": [0.1], "loss_before": 0.8, "loss_after": 0.6, "query_count": 10}
    assert accuracy([0, 1, 1], [0, 0, 1]) == 2/3
    checks = build_mechanism_checks(trace)
    assert checks["optimizer_step_executed"] is True
    assert checks["loss_decreased"] is True


def test_build_recovery_result_copies_target_metadata():
    target = {"dataset": "proxy", "metric": "accuracy", "paper_value": 0.7, "proxy": True}
    trace = {"params_before": [0.0], "params_after": [0.1], "loss_before": 0.8, "loss_after": 0.6, "query_count": 10}
    result = build_recovery_result("pid", target, [1], [1], trace, "python run.py", ["recovery/logs/training_trace.json"])
    assert result["paper_target"] == target
    assert result["metrics"]["accuracy"] == 1.0
