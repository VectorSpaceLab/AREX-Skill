import json
import tempfile
from pathlib import Path

from run_pope_recovery import run_proxy


def test_recovery_proxy_writes_artifacts():
    with tempfile.TemporaryDirectory() as tmp:
        attempt = Path(tmp)
        (attempt / "recovery" / "logs").mkdir(parents=True)
        (attempt / "module_plan.json").write_text(json.dumps({
            "paper_id": "pope_hallucination_eval",
            "fast_recovery_target": {"dataset": "synthetic", "metric": "f1", "paper_value": 0.7, "proxy": True},
        }), encoding="utf-8")
        skill_root = Path(__file__).resolve().parents[2]
        result = run_proxy(attempt, skill_root)
        assert result["is_proxy"] is True
        assert result["mechanism_checks"]["random_strategy_executed"] is True
        assert result["mechanism_checks"]["absent_negative_invariant_checked"] is True
        data_item = json.loads((attempt / "recovery" / "logs" / "generated_data_item.json").read_text(encoding="utf-8"))
        assert sorted(data_item["strategies"].keys()) == ["adversarial", "popular", "random"]
        assert all(value["metrics"]["f1"] >= 0.8 for value in data_item["strategies"].values())
        assert (attempt / "recovery" / "recovery_result.json").exists()
        assert (attempt / "recovery" / "logs" / "generated_skill_invocations.json").exists()
