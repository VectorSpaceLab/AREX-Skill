from sharpness_aware_update import sam_update

def test_sam_update_perturbs_and_updates():
    result = sam_update({'w': 1.0}, {'w': 2.0}, {'w': 0.5}, rho=0.1, lr=0.2)
    assert result['params_perturbed']['w'] > 1.0
    assert result['params_after']['w'] == 0.9
    assert result['perturbation_norm'] > 0


def test_zero_gradient_has_no_perturbation():
    result = sam_update({'w': 1.0}, {'w': 0.0}, {'w': 0.0}, rho=0.1, lr=0.2)
    assert result['params_perturbed']['w'] == 1.0
    assert result['params_after']['w'] == 1.0
