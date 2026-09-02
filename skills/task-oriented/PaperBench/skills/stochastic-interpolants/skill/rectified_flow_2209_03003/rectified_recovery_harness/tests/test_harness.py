from pathlib import Path

def test_harness_script_exists():
    assert (Path(__file__).resolve().parents[1] / 'scripts' / 'harness.py').exists()
