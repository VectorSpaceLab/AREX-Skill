from protocol import build_protocol, metric_gap

def test_rejects_label_mismatch():
    try:
        build_protocol([{"label":"cat"}], [{"label":"dog"}], "error", "lower_is_better", "rendition")
    except ValueError as exc:
        assert "outside clean" in str(exc)
    else:
        raise AssertionError("expected mismatch rejection")

def test_gap_direction():
    assert metric_gap(0.1, 0.4, "lower_is_better") == 0.30000000000000004
    assert metric_gap(0.8, 0.5, "higher_is_better") == 0.30000000000000004
