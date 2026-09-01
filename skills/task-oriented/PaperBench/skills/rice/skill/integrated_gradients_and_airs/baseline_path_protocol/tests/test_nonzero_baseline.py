from baseline_path import build_straightline_path


def test_nonzero_baseline_is_preserved():
    result = build_straightline_path([3], [1], 2)
    assert result['points'][0]['point'] == [2.0]
    assert result['points'][1]['point'] == [3.0]
