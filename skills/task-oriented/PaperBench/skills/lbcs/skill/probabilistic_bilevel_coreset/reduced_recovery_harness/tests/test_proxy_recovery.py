import json, tempfile
from pathlib import Path
from run_proxy_recovery import run


def test_proxy_recovery_runs_with_mechanism_checks():
    attempt = Path(tempfile.mkdtemp())
    (attempt / 'recovery' / 'logs').mkdir(parents=True)
    target = {'dataset': 'synthetic_noisy_imbalanced_binary_classification', 'split': 'test', 'metric': 'relative_validation_loss_improvement', 'paper_value': 0.0, 'proxy': True, 'rationale': 'test'}
    (attempt / 'module_plan.json').write_text(json.dumps({'fast_recovery_target': target}))
    skills_root = Path(__file__).resolve().parents[2]
    result = run(attempt, skills_root)
    assert isinstance(result['metrics']['relative_validation_loss_improvement'], float)
    assert result['mechanism_checks']['reduced_training_executed'] is True
    assert (attempt / 'recovery' / 'logs' / 'training_trace.json').exists()
