import subprocess, sys, pathlib, json

def test_recovery_script_exists():
    p=pathlib.Path(__file__).resolve().parents[1]/'scripts'/'run_proxy.py'
    assert p.exists()
    assert 'source_repo_read' in p.read_text()
