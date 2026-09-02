from hessian_metric import rank_candidates, weighted_loss_and_grad

def test_high_gradient_coordinate_dominates():
    ranked=rank_candidates([0,1], [('bad_high',[0,0.7]), ('bad_low',[0.3,1])], [1,10])
    assert ranked[0]['name']=='bad_low'

def test_optimizer_signal_changes_loss():
    loss,grad=weighted_loss_and_grad(1.0,[1,2],[1,1],[1,1])
    loss2,_=weighted_loss_and_grad(1.0-0.1*grad,[1,2],[1,1],[1,1])
    assert loss2 < loss
