from __future__ import annotations


def _floats(values):
    return [float(v) for v in values]


def integrated_gradients(gradient_fn, input_vector, baseline_vector, steps=50, output_fn=None):
    x = _floats(input_vector)
    baseline = _floats(baseline_vector)
    if not x:
        raise ValueError('input_vector must be non-empty')
    if len(x) != len(baseline):
        raise ValueError('input_vector and baseline_vector must have the same length')
    steps = int(steps)
    if steps <= 0:
        raise ValueError('steps must be positive')
    total_grad = [0.0] * len(x)
    for k in range(1, steps + 1):
        alpha = k / steps
        point = [b + alpha * (a - b) for a, b in zip(x, baseline)]
        grad = _floats(gradient_fn(point))
        if len(grad) != len(x):
            raise ValueError('gradient_fn returned wrong dimension')
        total_grad = [g0 + g1 for g0, g1 in zip(total_grad, grad)]
    avg_grad = [g / steps for g in total_grad]
    attributions = [(a - b) * g for a, b, g in zip(x, baseline, avg_grad)]
    result = {'attributions': attributions, 'attribution_sum': sum(attributions), 'steps': steps}
    if output_fn is not None:
        output_difference = float(output_fn(x)) - float(output_fn(baseline))
        result['output_difference'] = output_difference
        result['completeness_error'] = abs(result['attribution_sum'] - output_difference)
    return result


def finite_difference_gradient(output_fn, point, epsilon=1e-6):
    point = _floats(point)
    grads = []
    for i in range(len(point)):
        plus = list(point); minus = list(point)
        plus[i] += epsilon; minus[i] -= epsilon
        grads.append((float(output_fn(plus)) - float(output_fn(minus))) / (2 * epsilon))
    return grads
