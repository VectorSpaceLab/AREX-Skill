from lexiflow_recovery_evaluation import evaluate_recovery_trace


def test_recovery_metrics_pass_when_target_and_gain_hold():
    fake = {
        "lexiflow": {"best_objectives": [0.01, 0.04], "targets": [0.02, 0.04], "trace": [{"accepted": True, "candidates": [{"decision": {}}]}], "history": [{}, {}, {}]},
        "baseline": {"best_objectives": [0.0, 0.25], "history": [{}]},
    }
    result = evaluate_recovery_trace(fake)
    assert result["metrics"]["lexi_success_rate"] == 1.0
    assert result["mechanism_checks"]["lower_priority_improved_inside_target"]


def test_recovery_metrics_fail_without_lower_priority_gain():
    fake = {
        "lexiflow": {"best_objectives": [0.01, 0.40], "targets": [0.02, 0.40], "trace": [{"accepted": True, "candidates": [{}]}], "history": [{}, {}, {}]},
        "baseline": {"best_objectives": [0.0, 0.25], "history": [{}]},
    }
    result = evaluate_recovery_trace(fake)
    assert result["metrics"]["lexi_success_rate"] == 0.0

def test_recovery_metrics_fail_without_accepted_moves():
    fake = {
        "lexiflow": {"best_objectives": [0.01, 0.04], "targets": [0.02, 0.04], "trace": [{"accepted": False, "candidates": [{}]}], "history": [{}, {}, {}]},
        "baseline": {"best_objectives": [0.0, 0.25], "history": [{}]},
    }
    result = evaluate_recovery_trace(fake)
    assert result["metrics"]["lexi_success_rate"] == 0.0
