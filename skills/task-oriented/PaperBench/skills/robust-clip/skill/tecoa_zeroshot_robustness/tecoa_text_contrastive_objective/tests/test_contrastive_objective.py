from contrastive_objective import compute_tecoa_metrics


def test_aligned_pairs_have_lower_loss_than_swapped_pairs():
    images = [[1, 0], [0, 1]]
    texts = [[1, 0], [0, 1]]
    aligned = compute_tecoa_metrics(images, texts, [0, 1], temperature=0.5)
    swapped = compute_tecoa_metrics(images, texts, [1, 0], temperature=0.5)
    assert aligned["loss"] < swapped["loss"]
    assert aligned["accuracy"] == 1.0
    assert aligned["mean_margin"] > 0


def test_shape_and_label_validation():
    invalid_cases = [
        ([[1, 0]], [[1]], [0]),
        ([[1, 0]], [[1, 0]], [1]),
        ([[0, 0]], [[1, 0]], [0]),
    ]
    for images, texts, labels in invalid_cases:
        try:
            compute_tecoa_metrics(images, texts, labels)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid contrastive inputs should fail")


def test_temperature_scales_logits():
    cold = compute_tecoa_metrics([[1, 0]], [[1, 0], [0, 1]], [0], temperature=0.1)
    warm = compute_tecoa_metrics([[1, 0]], [[1, 0], [0, 1]], [0], temperature=1.0)
    assert cold["logits"][0][0] > warm["logits"][0][0]
