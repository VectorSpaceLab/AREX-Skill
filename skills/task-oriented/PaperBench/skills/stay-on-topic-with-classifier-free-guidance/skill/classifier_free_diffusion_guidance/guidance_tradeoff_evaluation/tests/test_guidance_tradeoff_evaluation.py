from tradeoff_eval import evaluate_tradeoff

def test_tradeoff_score():
    r=evaluate_tradeoff({0.0:[-1,0,3,4], 2.0:[1.8,2.0,2.2,2.1]}, 2.0)
    assert r['confidence_increased'] is True
    assert r['diversity_decreased'] is True
    assert r['guidance_tradeoff_score']==1.0
