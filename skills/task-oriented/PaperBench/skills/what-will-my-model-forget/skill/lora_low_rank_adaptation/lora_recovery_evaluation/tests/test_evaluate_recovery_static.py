from pathlib import Path

def test_harness_mentions_required_artifacts():
    skill_dir = Path(__file__).resolve().parents[1]
    text = (skill_dir / 'scripts' / 'evaluate_recovery.py').read_text()
    assert 'training_trace.json' in text
    assert 'lora_training_step' in text
