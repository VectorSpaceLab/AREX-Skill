from ppo_update import ppo_scalar_update


def test_ppo_scalar_update_changes_parameter():
    result = ppo_scalar_update(0.0, [0.0, -0.1, -0.2], [1.0, 0.5, 0.25])
    assert result['optimizer_state_changed']
    assert result['params_before'] != result['params_after']
    assert 'loss_before' in result and 'loss_after' in result
