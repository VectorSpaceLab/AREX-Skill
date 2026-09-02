from metrics import evaluate

def test_perfect_ranking():
    r=evaluate([1,1,0,0], [0.9,0.8,0.2,0.1])
    assert r['auroc'] == 1.0
    assert r['aupr'] == 1.0

def test_reversed_ranking():
    r=evaluate([1,1,0,0], [0.1,0.2,0.8,0.9])
    assert r['auroc'] == 0.0
    assert r['aupr'] < 0.5

def test_tied_ranking():
    r=evaluate([1,0], [0.5,0.5])
    assert r['auroc'] == 0.5
    assert r['base_rate'] == 0.5


def test_all_ties_average_precision_regression():
    r=evaluate([1,0,1,0], [0.5,0.5,0.5,0.5])
    assert r['auroc'] == 0.5
    assert abs(r['aupr'] - ((1/1 + 2/3)/2)) < 1e-12
