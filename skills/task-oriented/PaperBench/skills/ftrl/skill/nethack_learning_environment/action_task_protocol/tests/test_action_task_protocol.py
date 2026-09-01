from action_task import valid_actions, step_position, staircase_reward, aggregate_success

def test_actions_and_staircase_reward():
    obs = {'agent':[0,0], 'stairs':[[1,0]], 'raw_rows':['@>.']}
    assert 'N' in valid_actions() and 'PRAY' in valid_actions()
    pos = step_position(obs, 'E')
    out = staircase_reward(obs, 'E', pos)
    assert out['success'] is True and out['done'] is True and out['reward'] > 0.9
    assert aggregate_success([out, {'success': False}]) == 0.5

def test_wall_blocks_move():
    obs = {'agent':[0,0], 'stairs':[], 'raw_rows':['@|.']}
    assert step_position(obs, 'E') == [0,0]


def test_unknown_action_rejected():
    from action_task import require_valid_action
    try:
        require_valid_action('TELEPORT_TO_GOAL')
    except ValueError as exc:
        assert 'unknown NLE action' in str(exc)
    else:
        raise AssertionError('expected invalid action rejection')
