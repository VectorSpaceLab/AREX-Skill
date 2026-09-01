from build_proxy_fixture import fixture

def test_fixture_shape_and_labels():
    data=fixture()
    assert len(data['logits']) == 12
    assert sum(data['labels_in_positive']) == 6
    assert data['is_resource_derived'] is False
