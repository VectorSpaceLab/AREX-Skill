import math

from adaptive_weights import compute_weights


def test_weight_ratios_are_invariant_to_common_trace_scale():
    base = compute_weights(202.0, 2.0, 200.0)
    scaled = compute_weights(404.0, 4.0, 400.0)
    assert math.isclose(base["lambda_b"], scaled["lambda_b"])
    assert math.isclose(base["lambda_r"], scaled["lambda_r"])
