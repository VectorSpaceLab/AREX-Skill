from two_loop_direction import lbfgs_direction

def test_empty_memory_is_steepest_descent():
    out = lbfgs_direction([2.0, -3.0], [])
    assert out["direction"] == [-2.0, 3.0]
    assert out["descent_dot"] < 0

def test_one_pair_matches_scaled_inverse_action():
    out = lbfgs_direction([4.0], [([2.0], [8.0])])
    assert abs(out["direction"][0] + 1.0) < 1e-12
    assert out["pair_count"] == 1
