from evaluate_control import evaluate

def test_evaluation_passes_for_controlled_gain():
    out=evaluate([0.4,0.2,0.2,0.2],[0.1,0.4,0.4,0.1],[1,2],0.25,2.0)
    assert out['target_mass_gain'] > 0.25
    assert out['passed']
