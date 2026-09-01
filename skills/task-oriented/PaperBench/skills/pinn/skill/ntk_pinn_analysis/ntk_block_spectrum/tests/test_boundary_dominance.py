from ntk_spectrum import compute_spectrum


def test_boundary_dominance_is_detected():
    result = compute_spectrum([[4.0, 0.0], [0.0, 4.0]], [[1.0, 0.0], [0.0, 1.0]])
    assert result["dominance"] == "boundary_dominates"
    assert result["trace_kuu"] > result["trace_krr"]
