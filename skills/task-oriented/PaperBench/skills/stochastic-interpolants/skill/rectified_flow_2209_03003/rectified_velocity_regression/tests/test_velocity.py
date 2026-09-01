from velocity import train

def test_train_changes_params_and_reduces_loss():
    records = [{'xt': [0.0], 't': 0.0, 'target_velocity': [1.0]}, {'xt': [1.0], 't': 1.0, 'target_velocity': [2.0]}]
    result = train(records, lr=0.1, steps=10)
    assert result['optimizer_state_changed'] is True
    assert result['loss_after'] < result['loss_before']
    assert result['params_before'] != result['params_after']
