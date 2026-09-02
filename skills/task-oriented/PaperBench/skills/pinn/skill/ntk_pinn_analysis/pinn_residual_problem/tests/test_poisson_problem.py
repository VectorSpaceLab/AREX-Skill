import math

from poisson_problem import build_problem, poisson_second_derivative


def test_poisson_problem_has_aligned_components():
    problem = build_problem(1.0, [0.25, 0.5, 0.75])
    assert problem["operator"] == "poisson_second_derivative"
    assert len(problem["boundary_points"]) == len(problem["boundary_targets"])
    assert len(problem["residual_points"]) == len(problem["residual_targets"])
    assert abs(problem["boundary_targets"][0]) < 1e-12
    assert abs(problem["boundary_targets"][1]) < 1e-12


def test_poisson_residual_sign_matches_second_derivative():
    value = poisson_second_derivative(0.5, 1.0)
    assert math.isclose(value, -math.pi * math.pi, rel_tol=1e-12)
