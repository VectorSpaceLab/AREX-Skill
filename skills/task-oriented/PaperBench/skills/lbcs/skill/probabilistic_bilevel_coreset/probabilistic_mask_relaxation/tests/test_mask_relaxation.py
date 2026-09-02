from mask_relaxation import initialize_probabilities, sample_mask, score_gradient


def test_initialization_respects_budget():
    probs = initialize_probabilities(5, 2)
    assert len(probs) == 5
    assert abs(sum(probs) - 2.0) < 1e-9


def test_sampling_is_binary_and_seeded():
    probs = [0.2, 0.8, 1.0]
    assert sample_mask(probs, seed=7) == sample_mask(probs, seed=7)
    assert set(sample_mask(probs, seed=7)).issubset({0, 1})


def test_score_gradient_is_finite():
    grads = score_gradient([0.0, 0.5, 1.0], [0, 1, 1])
    assert len(grads) == 3
    assert all(abs(value) < 1000001 for value in grads)
