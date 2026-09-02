import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_mechanism.py"
spec = importlib.util.spec_from_file_location("evaluate_mechanism", MODULE_PATH)
evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)


def passing_inputs():
    recovery = {"is_proxy": True, "metrics": {"batchot_transport_cost_reduction": 0.25}, "mechanism_checks": {key: True for key in evaluator.REQUIRED_CHECKS}}
    recovery["mechanism_checks"].update({"original_repo_read": False, "full_image_training_executed": False})
    trace = {"params_before": {"weights": [0.0]}, "params_after": {"weights": [0.1]}, "loss_before": 1.0, "loss_after": 0.8}
    invocations = {"invocations": [{"module_id": key} for key in evaluator.REQUIRED_MODULES]}
    return recovery, trace, invocations


def test_mechanism_report_accepts_complete_proxy_evidence():
    recovery, trace, invocations = passing_inputs()
    report = evaluator.evaluate(recovery, trace, invocations)
    assert report["ok"] is True


def test_mechanism_report_rejects_missing_optimizer_step():
    recovery, trace, invocations = passing_inputs()
    recovery["mechanism_checks"]["optimizer_step_executed"] = False
    report = evaluator.evaluate(recovery, trace, invocations)
    assert report["ok"] is False
    assert any("optimizer_step" in failure for failure in report["failures"])
