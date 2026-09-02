import json
import tempfile
from pathlib import Path

from run_reduced_cic_recovery import run_reduced_recovery


def test_harness_writes_core_artifacts():
    with tempfile.TemporaryDirectory() as tmp:
        attempt = Path(tmp) / "attempt"
        skill_root = Path(__file__).resolve().parents[2]
        (attempt / "environment").mkdir(parents=True)
        (attempt / "modules").mkdir()
        (attempt / "module_plan.json").write_text(json.dumps({
            "paper_id": "cic_contrastive_goal_rl",
            "fast_recovery_target": {
                "dataset": "synthetic_state_transition_skill_pairs",
                "split": "deterministic_8_pair_proxy",
                "metric": "positive_logit_margin_after_update",
                "paper_value": 0.0,
                "proxy": True,
                "rationale": "test"
            }
        }), encoding="utf-8")
        (attempt / "environment" / "runtime_handoff.json").write_text("{}", encoding="utf-8")
        result = run_reduced_recovery(attempt, skill_root, seed=5)
        assert result["mechanism_checks"]["reduced_training_executed"] is True
        assert (attempt / "recovery" / "logs" / "training_trace.json").exists()
        assert (attempt / "recovery" / "logs" / "generated_skill_invocations.json").exists()
        assert result["metrics"]["loss_reduction"] >= -1e-6
