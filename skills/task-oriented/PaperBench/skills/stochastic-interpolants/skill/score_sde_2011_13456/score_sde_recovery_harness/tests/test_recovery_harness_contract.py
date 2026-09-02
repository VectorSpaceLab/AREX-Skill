from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]


def test_harness_script_exists():
    assert (SKILL_ROOT / "scripts" / "run_recovery.py").exists()


def test_skill_mentions_validator_artifacts():
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "recovery_result" in text
    assert "training trace" in text.lower()
