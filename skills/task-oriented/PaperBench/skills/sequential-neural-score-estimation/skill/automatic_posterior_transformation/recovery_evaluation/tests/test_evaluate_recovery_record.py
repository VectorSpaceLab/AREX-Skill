from evaluate_recovery_record import evaluate, REQUIRED

def test_evaluation_requires_mechanism_flags():
    rec={'metrics':{'posterior_mean_abs_error':0.1},'paper_target':{'metric':'posterior_mean_abs_error'},'mechanism_checks':{k:True for k in REQUIRED}}
    assert evaluate(rec, {'ok':True})['status'] == 'accept'
    rec['mechanism_checks']['atomic_loss_computed'] = False
    assert evaluate(rec, {'ok':True})['status'] == 'refine'

from evaluate_recovery_record import source_boundary_ok

def test_source_boundary_rejects_repo_path():
    assert source_boundary_ok({'original_repo_used': False, 'allowed_sources_used': ['paper_profile.md']})
    assert not source_boundary_ok({'original_repo_used': False, 'allowed_sources_used': ['/tmp/original_repo/file.py']})

from evaluate_recovery_record import invocation_coverage

def test_invocation_coverage_reports_missing_modules():
    out=invocation_coverage({'invocations':[{'module':'a'}]}, ['a','b'])
    assert not out['ok'] and out['missing'] == ['b']
