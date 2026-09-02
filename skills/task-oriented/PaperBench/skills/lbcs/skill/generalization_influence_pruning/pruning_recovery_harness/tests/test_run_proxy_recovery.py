import pathlib
script=pathlib.Path(__file__).resolve().parents[1]/'scripts'/'run_proxy_recovery.py'
text=script.read_text()
assert 'generated_skill_invocations.json' in text
assert 'optimizer_step_executed' in text
assert 'full_cifar_training_executed' in text
