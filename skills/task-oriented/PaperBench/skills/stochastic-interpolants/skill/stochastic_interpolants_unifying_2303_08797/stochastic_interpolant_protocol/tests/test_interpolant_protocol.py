from interpolant_protocol import construct_interpolant, gamma_quadratic


def test_endpoint_constraints_and_midpoint_derivative():
    start = construct_interpolant([1.0], [5.0], [0.0], [7.0])
    end = construct_interpolant([1.0], [5.0], [1.0], [7.0])
    mid = construct_interpolant([1.0], [5.0], [0.5], [2.0])
    assert start["x_t"] == [1.0]
    assert end["x_t"] == [5.0]
    assert gamma_quadratic(0.0) == 0.0
    assert gamma_quadratic(1.0) == 0.0
    assert mid["x_t"] == [4.0]
    assert mid["dot_x_t"] == [4.0]


def test_rejects_bad_time_shape():
    try:
        construct_interpolant([0.0, 1.0], [1.0, 2.0], [0.1, 0.2, 0.3], [0.0, 0.0])
    except ValueError as exc:
        assert "times" in str(exc)
    else:
        raise AssertionError("expected invalid time shape to fail")


def test_accepts_per_sample_times():
    result = construct_interpolant([0.0, 0.0], [2.0, 4.0], [0.25, 0.75], [0.0, 0.0])
    assert result["x_t"] == [0.5, 3.0]
    assert result["dot_x_t"] == [2.0, 4.0]
