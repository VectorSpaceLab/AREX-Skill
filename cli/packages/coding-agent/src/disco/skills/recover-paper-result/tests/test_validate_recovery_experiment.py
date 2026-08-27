import json
import tempfile
from pathlib import Path

from validate_recovery_experiment import main


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def make_valid_attempt(root):
    recovery = root / "recovery"
    logs = recovery / "logs"
    logs.mkdir(parents=True)
    (recovery / "experiment_plan.md").write_text("# Experiment Plan\n", encoding="utf-8")
    write_json(
        logs / "experiment_command_log.json",
        {"commands": [{"command": "python recovery/run_recovery.py", "returncode": 0, "status": "completed"}]},
    )
    write_json(
        logs / "generated_skill_invocations.json",
        {"invocations": [{"module": "loss_skill", "evidence": "called script", "log": "recovery/logs/loss_check.json"}]},
    )
    write_json(logs / "loss_check.json", {"ok": True})
    write_json(
        logs / "generated_data_item.json",
        {"is_resource_derived": True, "resource_files": [str(logs / "resource.txt")]},
    )
    (logs / "resource.txt").write_text("resource", encoding="utf-8")
    write_json(
        logs / "training_trace.json",
        {
            "loss_before": 1.0,
            "loss_after": 0.8,
            "params_before": {"w": 0.0},
            "params_after": {"w": 1.0},
            "optimizer_state_changed": True,
        },
    )
    write_json(recovery / "source_manifest.json", {"forbidden_sources_detected": []})
    write_json(
        recovery / "recovery_result.json",
        {
            "is_proxy": True,
            "metrics": {"proxy": 1.0},
            "commands": ["python recovery/run_recovery.py"],
            "mechanism_checks": {
                "reduced_training_executed": True,
                "optimizer_step_executed": True,
                "training_step_executed": False,
                "qwen3_model_loaded": False,
            },
        },
    )


def test_valid_reduced_recovery_gate_passes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_valid_attempt(root)
        assert main([str(root)]) == 0


def test_missing_experiment_command_log_fails():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_valid_attempt(root)
        (root / "recovery/logs/experiment_command_log.json").unlink()
        assert main([str(root)]) == 2
