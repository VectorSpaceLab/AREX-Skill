import json
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from check_recovery_artifacts import main


def test_check_recovery_artifacts_accepts_complete_minimal_tree():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for rel in [
            "recovery/experiment_plan.md",
            "recovery/logs/experiment_command_log.json",
            "recovery/logs/generated_skill_invocations.json",
            "recovery/logs/generated_data_item.json",
            "recovery/logs/training_trace.json",
        ]:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}" if path.suffix == ".json" else "plan", encoding="utf-8")
        result = {
            "metrics": {"posterior_mean_abs_error": 0.1},
            "mechanism_checks": {
                "proposal_rounds_executed": True,
                "posterior_transformation_executed": True,
                "atomic_loss_executed": True,
                "optimizer_step_executed": True,
            },
        }
        (root / "recovery/recovery_result.json").write_text(json.dumps(result), encoding="utf-8")
        manifest = {
            "forbidden_sources_detected": [],
            "runtime_handoff": "environment/runtime_handoff.json",
        }
        (root / "recovery/source_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with redirect_stdout(StringIO()):
            assert main(["--attempt-dir", str(root)]) == 0


def test_check_recovery_artifacts_rejects_forbidden_source_manifest():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for rel in [
            "recovery/experiment_plan.md",
            "recovery/logs/experiment_command_log.json",
            "recovery/logs/generated_skill_invocations.json",
            "recovery/logs/generated_data_item.json",
            "recovery/logs/training_trace.json",
        ]:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}" if path.suffix == ".json" else "plan", encoding="utf-8")
        result = {
            "metrics": {"mechanism_score": 1.0},
            "mechanism_checks": {
                "proposal_rounds_executed": True,
                "posterior_transformation_executed": True,
                "atomic_loss_executed": True,
                "optimizer_step_executed": True,
            },
        }
        (root / "recovery/recovery_result.json").write_text(json.dumps(result), encoding="utf-8")
        manifest = {
            "forbidden_sources_detected": ["/tmp/original_repo_should_not_be_used"],
            "runtime_handoff": "environment/runtime_handoff.json",
        }
        (root / "recovery/source_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with redirect_stdout(StringIO()):
            assert main(["--attempt-dir", str(root)]) == 2
