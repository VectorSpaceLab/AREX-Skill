from soft_regularization import soft_movement_regularization

def test_zero_and_downward():
    z=soft_movement_regularization([0], lambda_mvp=0)
    assert z['penalty']==0 and z['gradient']==[0]
    r=soft_movement_regularization([0], lambda_mvp=2, lr=1)
    assert abs(r['penalty']-1.0)<1e-9
    assert r['scores_after_reg_step'][0] < 0
