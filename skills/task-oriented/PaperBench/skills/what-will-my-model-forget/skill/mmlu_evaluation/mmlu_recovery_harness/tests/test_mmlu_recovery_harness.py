import subprocess, sys, tempfile, json
def test_harness_help_runs():
    import pathlib
    script=pathlib.Path(__file__).resolve().parents[1]/'scripts'/'run_recovery.py'
    proc=subprocess.run([sys.executable,str(script),'--help'],text=True,capture_output=True,timeout=20)
    assert proc.returncode==0 and '--attempt-dir' in proc.stdout
