import math

from adaptive_weights import compute_weights


def test_trace_ratio_weights_match_algorithm_one():
    result = compute_weights(202.0, 2.0, 200.0)
    assert math.isclose(result["lambda_b"], 101.0)
    assert math.isclose(result["lambda_r"], 1.01)
    assert result["stronger_weight"] == "boundary"


def test_degenerate_trace_is_rejected():
    try:
        compute_weights(1.0, 0.0, 1.0)
    except ValueError as exc:
        assert "trace_kuu" in str(exc)
    else:
        raise AssertionError("expected degenerate trace error")
