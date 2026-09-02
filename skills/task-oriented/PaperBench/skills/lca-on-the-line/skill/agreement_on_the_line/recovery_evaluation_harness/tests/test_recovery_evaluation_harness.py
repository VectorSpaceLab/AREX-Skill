import importlib.util
import json
import tempfile
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "recovery_evaluation_harness.py"
spec = importlib.util.spec_from_file_location("recovery_evaluation_harness", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_evaluate_computes_mae_and_checks():
    table = {
        "models": ["a", "b", "c"],
        "ood_predictions": {"a": [1, 1, 1, 0], "b": [1, 1, 0, 0], "c": [1, 0, 0, 0]},
        "evaluation_only": {"ood_labels": [1, 1, 0, 0]},
        "metadata": {"ood_labels_allowed_for_estimator": False},
    }
    estimate = {"predicted_ood_accuracy": {"a": 0.75, "b": 1.0, "c": 0.75}, "equation_count": 3}
    result = mod.evaluate(table, estimate, {"r2": 0.99, "on_line": True})
    assert abs(result["mae_percent"] - (abs(0.75 - 0.75) + abs(1.0 - 1.0) + abs(0.75 - 0.75)) * 100 / 3) < 1e-9
    assert result["mechanism_checks"]["ood_labels_withheld_from_estimator"] is True
