from conditioning_dropout import apply_conditioning_dropout, tiny_loss_update

def test_dropout_bounds_and_counts():
    r=apply_conditioning_dropout([0,1,2,3],1.0,seed=1)
    assert r['conditions']==['null']*4 and r['null_count']==4
    try:
        apply_conditioning_dropout([1],1.2)
        assert False
    except ValueError:
        pass

def test_tiny_update_decreases_loss():
    r=tiny_loss_update({'cond':0.0,'uncond':0.0},1.0,0.4,lr=0.2)
    assert r['loss_after'] < r['loss_before']
    assert r['params_before'] != r['params_after']
