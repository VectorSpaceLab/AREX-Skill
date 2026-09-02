from wild_stream_protocol import deterministic_proxy_stream

def test_proxy_stream_metadata():
    stream = deterministic_proxy_stream()
    assert stream['batch_size'] == 1
    assert stream['is_mixed_domain'] is True
    assert stream['is_label_imbalanced'] is True
    assert len(stream['samples']) == 12
