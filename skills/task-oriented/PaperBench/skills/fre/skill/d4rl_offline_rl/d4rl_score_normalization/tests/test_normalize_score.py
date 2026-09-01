from normalize_score import normalize_score


def test_endpoints_and_midpoint():
    assert normalize_score(0, 0, 10)["normalized_score"] == 0.0
    assert normalize_score(10, 0, 10)["normalized_score"] == 100.0
    assert normalize_score(5, 0, 10)["normalized_score"] == 50.0


def test_extrapolation_is_flagged_not_clipped():
    result = normalize_score(12, 0, 10)
    assert result["normalized_score"] == 120.0
    assert result["diagnostics"]["above_expert"] is True


def test_zero_denominator_rejected():
    try:
        normalize_score(1, 1, 1)
    except ValueError as exc:
        assert "must differ" in str(exc)
    else:
        raise AssertionError("expected ValueError")
