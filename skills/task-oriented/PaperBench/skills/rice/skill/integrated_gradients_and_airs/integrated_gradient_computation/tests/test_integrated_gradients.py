from integrated_gradients import finite_difference_gradient, integrated_gradients


def test_linear_function_exact():
    result = integrated_gradients(lambda p: [2.0, -1.0], [3, 4], [0, 0], 5, lambda p: 2*p[0]-p[1])
    assert result['attributions'] == [6.0, -4.0]
    assert result['completeness_error'] < 1e-12


def test_relu_sensitivity_saturation_case():
    def f(p):
        return max(1.0 - p[0], 0.0)
    def grad(p):
        return [-1.0 if p[0] < 1.0 else 0.0]
    result = integrated_gradients(grad, [1.0], [0.0], 200, f)
    assert abs(result['attribution_sum'] + 1.0) < 0.01


def test_finite_difference_gradient():
    grad = finite_difference_gradient(lambda p: p[0] * p[0] + p[1], [3, 2])
    assert abs(grad[0] - 6.0) < 1e-4
    assert abs(grad[1] - 1.0) < 1e-4
