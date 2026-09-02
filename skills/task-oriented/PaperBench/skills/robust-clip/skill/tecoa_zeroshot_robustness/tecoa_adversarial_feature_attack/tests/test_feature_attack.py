from feature_attack import generate_feature_attack
from contrastive_objective import compute_tecoa_metrics


def test_attack_respects_linf_bound_and_preserves_clean_input():
    images = [[1.0, 0.0], [0.0, 1.0]]
    original = [row[:] for row in images]
    result = generate_feature_attack(images, [[1, 0], [0, 1]], [0, 1], epsilon=0.15, step_size=0.1, steps=2, temperature=0.5)
    assert images == original
    assert result["bound_checks"]["passed"]
    assert result["bound_checks"]["max_abs_delta"] <= 0.150000001
    assert len(result["loss_trace"]) == 2


def test_attack_does_not_decrease_contrastive_loss():
    images = [[1.0, 0.0], [0.0, 1.0]]
    texts = [[1, 0], [0, 1]]
    baseline = compute_tecoa_metrics(images, texts, [0, 1], temperature=0.5)["loss"]
    result = generate_feature_attack(images, texts, [0, 1], epsilon=0.2, step_size=0.1, steps=3, temperature=0.5)
    assert result["loss_trace"][-1] >= baseline


def test_zero_epsilon_is_bounded_noop():
    result = generate_feature_attack([[1.0, 0.0]], [[1, 0], [0, 1]], [0], epsilon=0.0, step_size=0.1, steps=2, temperature=0.5)
    assert result["bound_checks"]["passed"]
    assert result["bound_checks"]["max_abs_delta"] == 0.0
    assert result["delta"] == [[0.0, 0.0]]


def test_invalid_attack_parameters_fail():
    cases = [(-1, 0.1, 1), (0.1, 0, 1), (0.1, 0.1, 0)]
    for epsilon, step_size, steps in cases:
        try:
            generate_feature_attack([[1, 0]], [[1, 0]], [0], epsilon, step_size, steps)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid attack parameters should fail")
