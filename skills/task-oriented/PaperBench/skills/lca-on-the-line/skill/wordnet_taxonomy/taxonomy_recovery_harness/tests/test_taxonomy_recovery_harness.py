from pathlib import Path


def test_harness_script_exists():
    skill_dir = Path(__file__).resolve().parents[1]
    assert (skill_dir / "scripts" / "recovery_harness.py").exists()
    text = (skill_dir / "SKILL.md").read_text()
    assert "soft-mode proxy" in text


def test_skill_documents_invocation_evidence_contract():
    skill_dir = Path(__file__).resolve().parents[1]
    text = (skill_dir / 'SKILL.md').read_text()
    assert 'generated_skill_invocations.json' in text
    assert 'training_trace.json' in text
    assert 'recovery_result.json' in text
