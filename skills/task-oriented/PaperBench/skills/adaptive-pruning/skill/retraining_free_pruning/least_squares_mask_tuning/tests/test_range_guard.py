from least_squares_mask_tuning import tune

def test_range_guard_rejects_extreme_coefficients():
    got=tune([[1]], [100], [1], damp=0.0, value_range=(-10,10))
    assert not got['accepted']
    assert got['reason'] == 'range_guard'
