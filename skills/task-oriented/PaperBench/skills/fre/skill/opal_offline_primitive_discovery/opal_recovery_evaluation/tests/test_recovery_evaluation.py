from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluate_opal_recovery import evaluate_recovery


def complete_inputs():
    plan = {"fast_recovery_target": {"dataset": "synthetic", "metric": "proxy_success_rate", "paper_value": 0.8}}
    checks = {
        "offline_segments_constructed": True,
        "primitive_autoencoding_loss_computed": True,
        "prior_matching_penalty_computed": True,
        "optimizer_step_executed": True,
        "latent_relabeling_executed": True,
        "high_level_latent_control_executed": True,
        "temporal_abstraction_verified": True,
    }
    result = {"is_proxy": True, "paper_target": {"dataset": "synthetic", "metric": "proxy_success_rate", "paper_value": 0.8}, "metrics": {"proxy_success_rate": 1.0}, "mechanism_checks": checks}
    manifest = {"sources": [{"role": "paper", "path": "paper.pdf"}]}
    invocations = {"invocations": [{"module_id": "offline_segment_protocol", "evidence_type": "called script"}]}
    return plan, result, manifest, invocations


def test_complete_proxy_passes():
    assert evaluate_recovery(*complete_inputs())["ok"] is True


def test_missing_mechanism_fails():
    plan, result, manifest, invocations = complete_inputs()
    result["mechanism_checks"].pop("optimizer_step_executed")
    evaluated = evaluate_recovery(plan, result, manifest, invocations)
    assert evaluated["ok"] is False
    assert "optimizer_step_executed" in evaluated["missing_mechanism_checks"]


if __name__ == "__main__":
    test_complete_proxy_passes()
    test_missing_mechanism_fails()
