from symbolic_observation import parse_grid, manhattan_to_stairs

def test_parse_grid_and_distance():
    obs = parse_grid(['@..', '.|.', '..>'], message='That door is closed.', blstats={'hp': 14})
    assert obs['agent'] == [0, 0]
    assert obs['stairs'] == [[2, 2]]
    assert obs['walkable_count'] == 8
    assert manhattan_to_stairs(obs) == 4

def test_rejects_bad_grid():
    try:
        parse_grid(['@.', '...'])
    except ValueError as exc:
        assert 'equal width' in str(exc)
    else:
        raise AssertionError('expected ValueError')


def test_missing_agent_is_rejected():
    try:
        parse_grid(['...', '..>'])
    except ValueError as exc:
        assert 'missing NetHack hero' in str(exc)
    else:
        raise AssertionError('expected missing hero rejection')
