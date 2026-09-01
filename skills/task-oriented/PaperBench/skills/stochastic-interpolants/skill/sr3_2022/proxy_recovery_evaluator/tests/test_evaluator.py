from evaluator import evaluate

def test_evaluator_requires_mechanism_evidence():
    pair = {'target': 1.0, 'is_proxy': True}
    trace = {'loss_before': 1.0, 'loss_after': 0.25, 'params_before': {'w': 0.0}, 'params_after': {'w': 1.0}}
    sampler = {'trajectory': [{'state': 0.2}, {'state': 0.8}], 'final': 0.9}
    out = evaluate(pair, trace, sampler)
    assert out['metrics']['loss_decrease'] > 0
    assert out['mechanism_checks']['optimizer_step_executed'] is True
    assert out['mechanism_checks']['iterative_refinement_executed'] is True
