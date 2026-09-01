from wanda import wanda_prune

def test_outlier_channel_is_preserved_by_wanda():
    weights=[[0.1, 9.0]]; norms=[100.0, 1.0]
    res=wanda_prune(weights, norms, 0.5)
    assert res['mask']==[[False, True]]
    assert res['pruned_weights'][0][0]==0.1
    assert res['pruned_weights'][0][1]==0.0
