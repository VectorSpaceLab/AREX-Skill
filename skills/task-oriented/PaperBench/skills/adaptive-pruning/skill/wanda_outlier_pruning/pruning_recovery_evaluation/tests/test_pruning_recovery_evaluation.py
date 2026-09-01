from evaluate import evaluate_pruning

def test_sparsity_and_invariants():
    res=evaluate_pruning([[1,2]], [[1,0]], [[1,1]], [[False, True]])
    assert res['sparsity']==0.5
    assert res['unmasked_weights_unchanged'] is True
    assert res['masked_weights_zero'] is True
    assert round(res['relative_output_error'],6)==round(2/3,6)
