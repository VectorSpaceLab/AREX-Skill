from cmaes_parameters import default_parameters

def test_default_parameters_are_normalized():
    params = default_parameters(2)
    assert params['lambda'] >= 2
    assert params['mu'] == params['lambda'] // 2
    assert abs(sum(params['weights']) - 1.0) < 1e-12
    assert 0 < params['c1'] < 1
    assert 0 <= params['cmu'] <= 1 - params['c1']
    assert params['ds'] > 0

def test_dimension_ten_has_expected_fields():
    params = default_parameters(10)
    assert params['dimension'] == 10
    assert params['mueff'] > 1
    assert params['expected_norm'] > 0


def test_dimension_one_edge_case_is_valid():
    params = default_parameters(1)
    assert params['dimension'] == 1
    assert params['lambda'] >= 2
    assert abs(sum(params['weights']) - 1.0) < 1e-12
