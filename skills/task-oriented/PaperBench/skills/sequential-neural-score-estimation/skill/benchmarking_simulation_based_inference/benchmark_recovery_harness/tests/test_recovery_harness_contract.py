import py_compile
from pathlib import Path


def test_harness_skill_has_expected_sections():
    text = Path(__file__).resolve().parents[1].joinpath("SKILL.md").read_text(encoding="utf-8")
    assert "source-boundary" in text or "source boundary" in text
    assert "validate_recovery_experiment.py" in text


def test_harness_script_compiles():
    script = Path(__file__).resolve().parents[1].joinpath("scripts/run_benchmark_recovery.py")
    py_compile.compile(str(script), doraise=True)


def test_harness_mentions_original_repository_exclusion():
    text = Path(__file__).resolve().parents[1].joinpath("SKILL.md").read_text(encoding="utf-8")
    assert "original repository" in text.lower() or "original repo" in text.lower()
