from cmaes_adaptation import adapt_paths_covariance

def test_adaptation_changes_sigma_and_keeps_spd():
    params = {'weights':[0.7,0.3], 'cs':0.4, 'ds':1.4, 'cc':0.6, 'c1':0.1, 'cmu':0.2, 'mueff':1.7, 'expected_norm':1.25}
    result = adapt_paths_covariance([0.0,0.0], [0.0,0.0], 0.5, [[1.0,0.0],[0.0,1.0]], [0.2,-0.1], [[0.2,-0.1],[0.1,0.3]], [[0.2,-0.1],[0.1,0.3]], params)
    assert result['sigma_changed']
    assert result['covariance_changed']
    assert min(result['eigenvalues']) > 0
