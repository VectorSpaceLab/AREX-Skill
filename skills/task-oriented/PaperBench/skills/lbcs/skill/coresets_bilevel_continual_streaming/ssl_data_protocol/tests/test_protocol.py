from protocol import build_protocol, deterministic_toy_protocol


def test_protocol_has_required_splits_and_weights():
    protocol = deterministic_toy_protocol()
    assert protocol['labeled'] and protocol['validation'] and protocol['unlabeled']
    assert set(protocol['weight_state']) == {item['id'] for item in protocol['unlabeled']}
    assert all(item['weight'] >= 0 for item in protocol['unlabeled'])


def test_duplicate_unlabeled_ids_are_rejected():
    try:
        build_protocol([{'x':[0], 'y':0}], [{'x':[1], 'y':1}], [{'id':'u', 'x':[0]}, {'id':'u', 'x':[1]}])
    except ValueError as exc:
        assert 'duplicate' in str(exc)
    else:
        raise AssertionError('duplicate ids should fail')
