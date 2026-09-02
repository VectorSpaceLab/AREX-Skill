import json
import tempfile
from pathlib import Path

from run_reduced_recovery import run


def test_reduced_recovery_writes_required_artifacts():
    with tempfile.TemporaryDirectory() as tmp:
        attempt = Path(tmp) / "attempt"
        skill_root = Path(__file__).resolve().parents[2]
        (attempt / "environment").mkdir(parents=True)
        (attempt / "environment" / "logs").mkdir(parents=True)
        (attempt / "modules").mkdir()
        (attempt / "paper_profile.md").write_text("profile", encoding="utf-8")
        (attempt / "module_plan.json").write_text(json.dumps({
            "fast_recovery_target": {
                "dataset": "synthetic_1d_gaussian_mixture",
                "split": "deterministic_16_sample_proxy",
                "metric": "epsilon_mse_reduction",
                "paper_value": 0.0,
                "proxy": True,
                "rationale": "test"
            }
        }), encoding="utf-8")
        (attempt / "environment" / "runtime_handoff.json").write_text(json.dumps({"runtime_ready": False}), encoding="utf-8")
        (attempt / "environment" / "logs" / "command_log.json").write_text(json.dumps({"commands": []}), encoding="utf-8")
        result = run(attempt, skill_root, learning_rate=0.1, steps=4)
        assert result["mechanism_checks"]["loss_decreased"] is True
        assert result["mechanism_checks"]["optimizer_step_executed"] is True
        assert (attempt / "recovery" / "logs" / "training_trace.json").exists()
        trace = json.loads((attempt / "recovery" / "logs" / "training_trace.json").read_text(encoding="utf-8"))
        assert trace["params_before"] != trace["params_after"]


def test_zero_learning_rate_preserves_parameters():
    from run_reduced_recovery import update

    params = {"a": 1.0, "b": -2.0, "c": 0.5}
    grads = {"a": 3.0, "b": 4.0, "c": -5.0}
    assert update(params, grads, 0.0) == params
