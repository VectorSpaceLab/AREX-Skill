import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_sil_recovery.py"
spec = importlib.util.spec_from_file_location("evaluate_sil_recovery", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def passing_payload():
    result = {
        "is_proxy": True,
        "metrics": {"sil_loss_decrease": 0.4},
        "mechanism_checks": {
            "replay_records_inserted": True,
            "positive_advantage_gate_checked": True,
            "sil_loss_computed": True,
            "optimizer_step_executed": True,
            "parameters_changed": True,
            "reduced_training_executed": True,
        },
    }
    command_log = {"commands": [{"returncode": 0}]}
    invocation_log = {"invocations": [{"skill": "x"}]}
    source_manifest = {"sources": ["paper_profile.md"]}
    return result, command_log, invocation_log, source_manifest


def test_passing_proxy_evidence():
    result, command_log, invocation_log, source_manifest = passing_payload()
    evaluation = mod.evaluate_sil_recovery(result, command_log, invocation_log, source_manifest, "/repo")
    assert evaluation["ok"] is True


def test_reject_missing_optimizer_evidence():
    result, command_log, invocation_log, source_manifest = passing_payload()
    result["mechanism_checks"]["optimizer_step_executed"] = False
    evaluation = mod.evaluate_sil_recovery(result, command_log, invocation_log, source_manifest)
    assert evaluation["ok"] is False


if __name__ == "__main__":
    test_passing_proxy_evidence()
    test_reject_missing_optimizer_evidence()
