import json
import tempfile
from pathlib import Path

from build_proxy_result import build_proxy_result


def test_build_proxy_result_combines_mechanism_checks():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        logs = root / "recovery" / "logs"
        logs.mkdir(parents=True)
        (root / "module_plan.json").write_text(json.dumps({
            "paper_id": "latent_diffusion_models",
            "fast_recovery_target": {"dataset": "synthetic", "metric": "ldm_loss_reduction", "paper_value": 0.0, "proxy": True}
        }), encoding="utf-8")
        (logs / "training_trace.json").write_text(json.dumps({
            "loss_before": 1.0,
            "loss_after": 0.5,
            "mechanism_checks": {"reduced_training_executed": True, "optimizer_step_executed": True}
        }), encoding="utf-8")
        (logs / "latent_contract.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
        (logs / "cross_attention.json").write_text(json.dumps({"conditioned": [[1.0]], "row_sums": [1.0]}), encoding="utf-8")
        (logs / "spatial_plan.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
        handoff = root / "environment" / "runtime_handoff.json"
        handoff.parent.mkdir()
        handoff.write_text(json.dumps({"runtime_ready": False, "blockers": ["missing checkpoint"]}), encoding="utf-8")
        result = build_proxy_result(root, root, handoff)
        assert result["is_proxy"] is True
        assert result["metrics"]["ldm_loss_reduction"] == 0.5
        assert result["mechanism_checks"]["cross_attention_conditioning_executed"] is True
        assert result["mechanism_checks"]["full_runtime_blocked"] is True
