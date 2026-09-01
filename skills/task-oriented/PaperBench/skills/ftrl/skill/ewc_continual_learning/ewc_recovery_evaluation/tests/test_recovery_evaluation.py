from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from recovery_evaluation import run_recovery


def test_reduced_recovery_runs_ewc_mechanism():
    skill_root = Path(__file__).resolve().parents[2]
    module_plan = {
        "fast_recovery_target": {
            "dataset": "synthetic_two_task_binary_classification",
            "split": "deterministic 8-example task-A and task-B reduced proxy",
            "metric": "retention_advantage",
            "paper_value": 0.0,
            "proxy": True,
            "rationale": "test fixture"
        }
    }
    outputs = run_recovery(skill_root, module_plan)
    result = outputs["result"]
    trace = outputs["trace"]
    assert result["mechanism_checks"]["fisher_estimated_from_task_a_gradients"] is True
    assert result["mechanism_checks"]["ewc_penalty_positive_during_task_b"] is True
    assert result["mechanism_checks"]["optimizer_step_executed"] is True
    assert result["metrics"]["retention_advantage"] > 0
    assert trace["params_before"] != trace["params_after"]
