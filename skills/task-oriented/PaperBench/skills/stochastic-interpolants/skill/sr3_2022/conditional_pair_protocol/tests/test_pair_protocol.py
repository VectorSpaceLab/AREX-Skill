from pair_protocol import build_pair, validate_pair

def test_build_pair_contract():
    pair = build_pair(1.0, scale_factor=4.0)
    assert pair['condition'] == 0.25
    assert pair['target'] == 1.0
    assert pair['is_proxy'] is True
    assert validate_pair(pair)
