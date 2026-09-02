from ntk_spectrum import compute_spectrum


def test_residual_dominance_is_detected():
    result = compute_spectrum([[1.0, 0.0], [0.0, 1.0]], [[10.0, 0.0], [0.0, 10.0]])
    assert result["trace_kuu"] == 2.0
    assert result["trace_krr"] == 200.0
    assert result["trace_full"] == 202.0
    assert result["dominance"] == "residual_dominates"


def test_balanced_blocks_are_detected():
    result = compute_spectrum([[1.0, 0.0]], [[0.0, 1.0]])
    assert result["dominance"] == "balanced"
