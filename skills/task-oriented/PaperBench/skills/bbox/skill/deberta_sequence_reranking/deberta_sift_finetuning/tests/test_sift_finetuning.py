from sift_finetuning import normalize_vector, perturb_normalized, train_step


def test_normalize_vector_has_unit_norm():
    normalized = normalize_vector([3.0, 4.0])
    assert round(sum(value * value for value in normalized), 8) == 1.0


def test_perturbation_changes_normalized_values():
    normalized = normalize_vector([1.0, 1.0])
    perturbed = perturb_normalized([1.0, 1.0], scale=0.1)
    assert perturbed != normalized
    assert abs(abs(perturbed[0] - normalized[0]) - 0.1) < 1e-12


def test_train_step_changes_params_and_loss():
    result = train_step([2.0, 1.0], {"w0": 0.1, "w1": -0.1, "bias": 0.0}, target=1.0)
    assert result["params_before"] != result["params_after"]
    assert result["loss_after"] < result["loss_before"]
