from least_squares_mask_tuning import tune

def test_tuning_reduces_error_and_keeps_pruned_zero():
    A=[[1,0,2],[0,1,1],[1,1,0]]; b=[2,1,2]
    got=tune(A,b,[1,0,1],damp=0.01)
    assert got['accepted']
    assert got['mask'][1] == 0
    assert got['tuned_error'] < got['baseline_error']
