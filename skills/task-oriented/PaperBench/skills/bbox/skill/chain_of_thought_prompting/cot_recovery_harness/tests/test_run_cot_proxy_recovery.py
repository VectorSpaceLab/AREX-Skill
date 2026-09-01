import tempfile
from pathlib import Path

from run_cot_proxy_recovery import run_recovery, write_json


def test_proxy_recovery_writes_result_with_mechanism_checks():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        attempt = root / "attempt"
        skills = root / "skills"
        attempt.mkdir()
        source_root = Path(__file__).resolve().parents[2]
        for name in ["cot_prompt_templates", "cot_answer_extraction", "cot_equation_calculator"]:
            (skills / name / "scripts").mkdir(parents=True)
            src = source_root / name / "scripts" / f"{name}.py"
            dst = skills / name / "scripts" / f"{name}.py"
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        write_json(
            attempt / "module_plan.json",
            {
                "paper_id": "chain_of_thought_prompting",
                "fast_recovery_target": {
                    "dataset": "GSM8K-style arithmetic proxy",
                    "split": "mini",
                    "metric": "accuracy",
                    "paper_value": 0.569,
                    "proxy": True,
                    "rationale": "test",
                },
            },
        )
        handoff = attempt / "environment" / "runtime_handoff.json"
        write_json(handoff, {"runtime_ready": False})
        result = run_recovery(attempt, skills, handoff)
        assert result["is_proxy"] is True
        assert result["metrics"]["accuracy"] == 1.0
        assert result["mechanism_checks"]["cot_accuracy_exceeds_standard"] is True
        assert (attempt / "recovery" / "logs" / "generated_skill_invocations.json").exists()
