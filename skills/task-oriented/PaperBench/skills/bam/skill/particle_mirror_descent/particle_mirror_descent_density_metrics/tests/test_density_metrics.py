from density_metrics import cross_entropy, symmetric_mode_coverage, total_variation


def test_mode_coverage_distinguishes_two_modes():
    particles = [[1.0, -2.0], [-1.0, 2.0], [1.1, -2.1], [-1.1, 2.1]]
    weights = [0.25, 0.25, 0.25, 0.25]
    metrics = symmetric_mode_coverage(particles, weights, [[1.0, -2.0], [-1.0, 2.0]], 0.5)
    assert metrics["covered_modes"] == 2
    assert metrics["mode_coverage_score"] == 1.0


def test_grid_metrics_are_finite_and_ordered():
    target = [[0.4, 0.1], [0.1, 0.4]]
    estimate = [[0.3, 0.2], [0.2, 0.3]]
    assert abs(total_variation(target, target, 1.0)) == 0.0
    assert total_variation(target, estimate, 1.0) > 0.0
    assert cross_entropy(target, estimate, 1.0) > 0.0
