from __future__ import annotations


def _as_float_list(values):
    return [float(v) for v in values]


def build_straightline_path(input_vector, baseline_vector, steps, baseline_score=None, near_zero_tolerance=1e-3):
    x = _as_float_list(input_vector)
    baseline = _as_float_list(baseline_vector)
    if not x:
        raise ValueError('input_vector must be non-empty')
    if len(x) != len(baseline):
        raise ValueError('input_vector and baseline_vector must have the same length')
    if int(steps) <= 0:
        raise ValueError('steps must be positive')
    steps = int(steps)
    deltas = [a - b for a, b in zip(x, baseline)]
    points = []
    for k in range(1, steps + 1):
        alpha = k / steps
        points.append({'alpha': alpha, 'point': [b + alpha * d for b, d in zip(baseline, deltas)]})
    warnings = []
    if baseline_score is not None and abs(float(baseline_score)) > near_zero_tolerance:
        warnings.append('baseline score is not near zero for the explained target')
    return {'input': x, 'baseline': baseline, 'steps': steps, 'points': points, 'warnings': warnings}
