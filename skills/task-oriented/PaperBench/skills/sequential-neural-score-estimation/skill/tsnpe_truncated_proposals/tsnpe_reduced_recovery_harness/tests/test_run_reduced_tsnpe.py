import subprocess, sys
from pathlib import Path

def test_harness_script_has_entrypoint():
    script=Path(__file__).resolve().parents[1] / 'scripts' / 'run_reduced_tsnpe.py'
    text=script.read_text()
    assert 'def main()' in text and 'recovery_result.json' in text

if __name__=='__main__': test_harness_script_has_entrypoint()
