from evaluate_proxy import evaluate_proxy

def test_accepts_complete_strong_proxy():
    checks={name:True for name in ['paired_records_validated','line_fit_executed','correlation_computed','residuals_inspected','proxy_declared','source_boundary_respected']}
    result=evaluate_proxy({'pearson_r':0.99}, checks, 0.95)
    assert result['accepted_proxy'] is True
    assert result['mechanism_ok'] is True

def test_rejects_missing_check():
    checks={'paired_records_validated':True}
    result=evaluate_proxy({'pearson_r':0.99}, checks, 0.95)
    assert result['accepted_proxy'] is False
    assert 'line_fit_executed' in result['missing_checks']


def test_rejects_below_threshold_metric():
    checks={name:True for name in ['paired_records_validated','line_fit_executed','correlation_computed','residuals_inspected','proxy_declared','source_boundary_respected']}
    result=evaluate_proxy({'pearson_r':0.80}, checks, 0.95)
    assert result['accepted_proxy'] is False
    assert result['metric_gap'] < 0
