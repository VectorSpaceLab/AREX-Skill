from actor_update import actor_update

def test_actor_update_changes_parameters():
    out=actor_update({'mean_weight':0.0,'log_std':-0.5}, state=1.0, noise=0.0, target_action=1.0, alpha=0.2, lr=0.1)
    assert out['params_before'] != out['params_after']
    assert out['action_after'] > out['action_before']

def test_actor_loss_is_numeric():
    out=actor_update({'mean_weight':0.2,'log_std':-1.0}, state=0.5, noise=0.3)
    assert isinstance(out['loss_before'], float)


def test_actor_update_with_nonzero_noise_changes_log_std():
    out=actor_update({'mean_weight':0.1,'log_std':-0.2}, state=1.0, noise=0.5, target_action=0.8, alpha=0.2, lr=0.05)
    assert out['params_before']['log_std'] != out['params_after']['log_std']
