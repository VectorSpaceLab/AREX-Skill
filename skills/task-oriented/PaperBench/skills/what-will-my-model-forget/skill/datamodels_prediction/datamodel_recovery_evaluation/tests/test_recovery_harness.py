import importlib.util
import json
import tempfile
from pathlib import Path

script_path = Path(__file__).resolve().parents[1] / "scripts" / "run_proxy_recovery.py"
spec = importlib.util.spec_from_file_location("run_proxy_recovery", script_path)
run_proxy_recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_proxy_recovery)


def test_run_proxy_recovery_writes_metrics():
    skills_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as tmpdir:
        attempt = Path(tmpdir)
        (attempt / "modules").mkdir()
        (attempt / "environment").mkdir()
        (attempt / "environment" / "runtime_handoff.json").write_text('{"runtime_ready": false}\n', encoding="utf-8")
        (attempt / "paper_profile.md").write_text("profile", encoding="utf-8")
        (attempt / "module_plan.json").write_text(json.dumps({
            "fast_recovery_target": {
                "dataset": "synthetic alpha-subset datamodel proxy",
                "split": "test",
                "metric": "pearson_correlation",
                "paper_value": 0.99,
                "proxy": True,
                "rationale": "test"
            }
        }), encoding="utf-8")
        result = run_proxy_recovery.run_proxy(str(attempt), str(skills_root), d=10, train_subsets=48, test_subsets=20, seed=5)
        assert result["metrics"]["pearson_correlation"] > 0.99
        assert result["mechanism_checks"]["generated_skills_invoked"] is True
        assert (attempt / "recovery" / "recovery_result.json").exists()


if __name__ == "__main__":
    test_run_proxy_recovery_writes_metrics()
