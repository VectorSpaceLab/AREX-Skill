from evaluation_protocol import example_protocol, validate_protocol


def test_proxy_protocol_passes():
    result = validate_protocol(example_protocol("proxy"))
    assert result["ok"] is True
    assert result["protocol"]["metric"] == "guided_distance_improvement"


def test_full_guided_protocol_requires_scale():
    result = validate_protocol(example_protocol("full_missing_scale"))
    assert result["ok"] is False
    assert "classifier_scale" in result["errors"][0]
