import math

from surrogate import clipped_surrogate


def close(left, right):
    return abs(left - right) < 1e-9


def test_positive_advantage_caps_high_ratio():
    result = clipped_surrogate([math.log(1.5)], [0.0], [2.0], 0.2)
    assert close(result["unclipped_terms"][0], 3.0)
    assert close(result["clipped_terms"][0], 2.4)
    assert close(result["selected_terms"][0], 2.4)


def test_negative_advantage_caps_low_ratio_pessimistically():
    result = clipped_surrogate([math.log(0.5)], [0.0], [-2.0], 0.2)
    assert close(result["unclipped_terms"][0], -1.0)
    assert close(result["clipped_terms"][0], -1.6)
    assert close(result["selected_terms"][0], -1.6)


def test_in_range_ratio_is_unchanged():
    result = clipped_surrogate([math.log(1.1)], [0.0], [3.0], 0.2)
    assert close(result["unclipped_terms"][0], result["clipped_terms"][0])
    assert close(result["clip_fraction"], 0.0)
