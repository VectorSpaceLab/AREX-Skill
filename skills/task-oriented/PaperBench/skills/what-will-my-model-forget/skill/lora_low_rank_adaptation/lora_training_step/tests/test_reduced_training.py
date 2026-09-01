from reduced_training import run

def test_reduced_training_decreases_loss_and_freezes_base():
    trace=run(steps=12, lr=0.1)
    assert trace['loss_after'] < trace['loss_before']
    assert trace['base_weight_unchanged']
    assert trace['params_before']['B'] != trace['params_after']['B']
    assert trace['merge_max_abs_diff'] < 1e-12
