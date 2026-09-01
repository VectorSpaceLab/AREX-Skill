from diffusion_objective import optimizer_step

def test_optimizer_step_decreases_loss():
    pair = {'condition': 0.25, 'target': 1.0}
    trace = optimizer_step(pair)
    assert trace['params_before'] != trace['params_after']
    assert trace['loss_after'] < trace['loss_before']
