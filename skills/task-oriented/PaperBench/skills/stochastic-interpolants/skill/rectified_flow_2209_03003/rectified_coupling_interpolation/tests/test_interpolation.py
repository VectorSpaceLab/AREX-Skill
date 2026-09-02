from interpolation import build_records

def test_interpolation_and_target_velocity():
    records = build_records([[0.0], [2.0]], [[2.0], [6.0]], [0.25, 0.5])
    assert records[0]['xt'] == [0.5]
    assert records[0]['target_velocity'] == [2.0]
    assert records[1]['xt'] == [4.0]
    assert records[1]['target_velocity'] == [4.0]
