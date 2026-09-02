import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "run_proxy_recovery.py"
spec = importlib.util.spec_from_file_location("run_proxy_recovery", script)
run_proxy_recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_proxy_recovery)


def test_proxy_recovery_writes_validator_artifacts():
    source_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as tmp:
        attempt = Path(tmp) / "attempt"
        skill_root = Path(tmp) / "skills"
        shutil.copytree(source_root / "conditional_ot_paths", skill_root / "conditional_ot_paths")
        shutil.copytree(source_root / "conditional_flow_matching_loss", skill_root / "conditional_flow_matching_loss")
        shutil.copytree(source_root / "cnf_ode_sampling", skill_root / "cnf_ode_sampling")
        attempt.mkdir()
        (attempt / "modules").mkdir()
        (attempt / "environment").mkdir()
        (attempt / "paper_profile.md").write_text("profile", encoding="utf-8")
        (attempt / "module_plan.json").write_text(json.dumps({
            "schema_version": 1,
            "paper_id": "flow_matching_2210_02747",
            "title": "Flow Matching for Generative Modeling",
            "fast_recovery_target": {
                "dataset": "synthetic_2d_ot_gaussian_mixture",
                "split": "deterministic_8_point_proxy",
                "metric": "midpoint_mse_to_analytic_ot_path",
                "paper_value": 0.0,
                "proxy": True,
                "rationale": "test"
            },
            "modules": []
        }), encoding="utf-8")
        (attempt / "environment" / "runtime_handoff.json").write_text(json.dumps({"environment_modified": False}), encoding="utf-8")
        result = run_proxy_recovery.run(attempt, skill_root)
        assert result["mechanism_checks"]["loss_decreased"] is True
        assert result["mechanism_checks"]["source_boundary_respected"] is True
        assert (attempt / "recovery" / "recovery_result.json").exists()
        assert (attempt / "recovery" / "logs" / "training_trace.json").exists()


if __name__ == "__main__":
    test_proxy_recovery_writes_validator_artifacts()
