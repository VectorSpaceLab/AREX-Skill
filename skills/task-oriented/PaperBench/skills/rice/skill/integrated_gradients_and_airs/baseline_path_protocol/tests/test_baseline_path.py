from baseline_path import build_straightline_path


def test_straightline_endpoint_and_spacing():
    result = build_straightline_path([2, 4], [0, 0], 4)
    assert [p['alpha'] for p in result['points']] == [0.25, 0.5, 0.75, 1.0]
    assert result['points'][-1]['point'] == [2.0, 4.0]


def test_rejects_bad_dimensions():
    try:
        build_straightline_path([1], [0, 0], 2)
    except ValueError as exc:
        assert 'same length' in str(exc)
    else:
        raise AssertionError('expected dimension failure')


def test_baseline_warning():
    result = build_straightline_path([1], [0], 2, baseline_score=0.2)
    assert result['warnings']
