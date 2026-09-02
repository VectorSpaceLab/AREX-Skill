from calibration import activation_norms

def test_l2_norms_and_outlier_order():
    res=activation_norms([[[3,1],[4,2],[0,10]]])
    assert res['activation_norms'][0]==5.0
    assert round(res['activation_norms'][1],6)==round((1+4+100)**0.5,6)
    assert res['metadata']['descending_channels'][0]==1
