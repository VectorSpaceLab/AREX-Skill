from run_proxy_recovery import optimizer_step, represented_fraction


def test_optimizer_step_changes_params_and_loss():
    trace = optimizer_step([0, 10, 30, 39], [0]*20 + [1]*20)
    assert trace['params_before'] != trace['params_after']
    assert trace['loss_after'] < trace['loss_before']


def test_represented_fraction_counts_bins():
    scores = [i / 7 for i in range(8)]
    frac, bins = represented_fraction([0, 3, 7], scores, 4)
    assert frac == 0.75
    assert bins == [0, 1, 3]
