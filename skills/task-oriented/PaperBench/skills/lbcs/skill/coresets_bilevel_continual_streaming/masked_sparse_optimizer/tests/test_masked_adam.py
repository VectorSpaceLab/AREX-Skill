from masked_adam import masked_adam_step


def test_unselected_entries_are_unchanged():
    weights = {'u0': 0.5, 'u1': 0.5}
    state = {'m': {'u1': 7.0}, 'v': {'u1': 9.0}, 't': {'u1': 3}}
    updated, new_state, diagnostics = masked_adam_step(weights, {'u0': 1.0}, state=state, lr=0.1)
    assert updated['u1'] == 0.5
    assert new_state['m']['u1'] == 7.0
    assert new_state['v']['u1'] == 9.0
    assert new_state['t']['u1'] == 3
    assert updated['u0'] < weights['u0']
    assert diagnostics[0]['id'] == 'u0'
