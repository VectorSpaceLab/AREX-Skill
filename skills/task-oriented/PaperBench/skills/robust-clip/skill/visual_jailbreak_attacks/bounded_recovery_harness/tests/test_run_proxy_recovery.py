import json
import tempfile
from pathlib import Path

from run_proxy_recovery import run_proxy_recovery


def test_proxy_recovery_writes_result():
    with tempfile.TemporaryDirectory() as tmp:
        attempt = Path(tmp) / "attempt"
        skills_root = Path(__file__).resolve().parents[2]
        (attempt / "environment").mkdir(parents=True)
        (attempt / "modules").mkdir()
        (attempt / "module_plan.json").write_text(json.dumps({
            "paper_id": "visual_jailbreak_attacks",
            "fast_recovery_target": {"dataset": "safe_symbolic_visual_jailbreak_proxy", "split": "tiny-heldout", "metric": "obedience_delta", "paper_value": 0.1, "proxy": True}
        }))
        (attempt / "paper_profile.md").write_text("profile")
        (attempt / "environment" / "runtime_handoff.json").write_text(json.dumps({"runtime_ready": False, "blockers": ["test"]}))
        result = run_proxy_recovery(attempt, skills_root)
        assert result["metrics"]["obedience_delta"] >= 0.1
        assert (attempt / "recovery" / "recovery_result.json").exists()
        manifest = json.loads((attempt / "recovery" / "source_manifest.json").read_text())
        assert manifest["forbidden_sources_detected"] == []
        assert manifest["original_repo_used_during_recovery"] is False
