from dlr import dlr_loss, diagnostics

def test_affine_invariance():
    base=dlr_loss([1.0,3.0,0.0],0)
    shifted=dlr_loss([12.0,16.0,10.0],0)
    assert abs(base-shifted) < 1e-9

def test_loss_increases_when_true_logit_drops():
    assert dlr_loss([2.5,2.0,0.0],0) < dlr_loss([1.0,2.0,0.0],0)
    assert diagnostics([1.0,2.0,0.0],0)['true_rank'] == 1
