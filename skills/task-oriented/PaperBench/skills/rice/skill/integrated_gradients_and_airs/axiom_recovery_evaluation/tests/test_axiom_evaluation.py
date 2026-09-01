from axiom_evaluation import evaluate_axioms


def test_accepts_complete_symmetric_result():
    result = evaluate_axioms([0.5, 0.5], 1.0, tolerance=1e-6, paired_attributions=[0.5, 0.5], symmetry_groups=[[0, 1]], sensitivity_attribution=0.5)
    assert result['proxy_accepted'] is True
    assert result['metrics']['completeness_error'] == 0.0


def test_rejects_bad_completeness():
    result = evaluate_axioms([0.2, 0.2], 1.0, tolerance=0.05)
    assert result['proxy_accepted'] is False
    assert result['mechanism_checks']['completeness_checked'] is False
