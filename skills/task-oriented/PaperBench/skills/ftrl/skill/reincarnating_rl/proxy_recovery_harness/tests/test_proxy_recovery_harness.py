import importlib.util
import json
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_proxy_recovery.py"
spec = importlib.util.spec_from_file_location("run_proxy_recovery", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_proxy_recovery_runs_and_writes_evidence():
    with tempfile.TemporaryDirectory() as tmp:
        attempt_dir = Path(tmp)
        (attempt_dir / "module_plan.json").write_text(json.dumps({
            "fast_recovery_target": {
                "dataset": "deterministic_tabular_pvrl_proxy",
                "metric": "loss_decrease_and_policy_match",
                "paper_value": 1.0,
                "proxy": True
            }
        }))
        skills_root = Path(__file__).resolve().parents[2]
        output = module.run_proxy(attempt_dir, skills_root, attempt_dir / "recovery")
        assert output["recovery_result"]["metrics"]["loss_decrease_and_policy_match"] == 1.0
        assert output["trace"]["loss_after"] < output["trace"]["loss_before"]
        assert output["trace"]["params_before"] != output["trace"]["params_after"]
        assert Path(output["paths"]["generated_data"]).exists()
        assert Path(output["paths"]["invocations"]).exists()


if __name__ == "__main__":
    test_proxy_recovery_runs_and_writes_evidence()
