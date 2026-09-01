from helmholtz_problem import build_problem, forcing, relative_l2

def test_problem_is_deterministic_and_scored():
    first = build_problem(seed=7, n_interior=5, n_boundary=8, n_eval_side=3)
    second = build_problem(seed=7, n_interior=5, n_boundary=8, n_eval_side=3)
    assert first == second
    assert len(first["boundary_values"]) == 8
    assert relative_l2(first["eval_values"], first["eval_values"]) == 0.0
    assert abs(forcing(0.2, 0.3)) > 1e-9
