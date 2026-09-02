from recovery_contract import mechanism_score, build_result, source_boundary_ok

def test_recovery_contract_fields():
    checks = {'hvp_executed': True, 'power_iteration_executed': True, 'hutchinson_trace_executed': True, 'slq_density_executed': True, 'architecture_comparison_executed': True, 'optimizer_step_executed': True}
    assert mechanism_score(checks) == 1.0
    target = {'dataset': 'proxy', 'metric': 'mechanism_score', 'paper_value': 1.0, 'proxy': True}
    result = build_result('pid', target, {'mechanism_score': 1.0}, checks, 'python run.py')
    assert result['is_proxy'] is True and result['metrics']['mechanism_score'] == 1.0
    assert source_boundary_ok(['paper.pdf', 'skills/x'], ['original_repo_path'])
