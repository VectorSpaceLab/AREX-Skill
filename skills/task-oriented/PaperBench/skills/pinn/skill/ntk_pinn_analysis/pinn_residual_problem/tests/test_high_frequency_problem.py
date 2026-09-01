import math

from poisson_problem import build_problem, poisson_second_derivative


def test_high_frequency_fixture_scales_forcing():
    problem = build_problem(2.0, [0.25])
    expected = poisson_second_derivative(0.25, 2.0)
    assert math.isclose(problem["residual_targets"][0], expected, rel_tol=1e-12)
    assert problem["frequency"] == 2.0
