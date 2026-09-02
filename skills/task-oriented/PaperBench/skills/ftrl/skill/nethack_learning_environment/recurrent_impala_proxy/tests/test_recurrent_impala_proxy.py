from impala_proxy import train_one_step

def test_train_one_step_changes_params_and_loss():
    trace = train_one_step({'bias':0.0, 'distance_weight':0.0}, {'distance_delta':1.0}, label=1, lr=0.2)
    assert trace['loss_after'] < trace['loss_before']
    assert trace['params_after'] != trace['params_before']


def test_negative_label_updates_away_from_action():
    from impala_proxy import train_one_step
    trace = train_one_step({'bias': 0.0, 'distance_weight': 0.0}, {'distance_delta': 1.0}, label=0, lr=0.2)
    assert trace['loss_after'] < trace['loss_before']
    assert trace['params_after']['bias'] < trace['params_before']['bias']
