from score_sde_schedule import ve_sigma, reverse_score_drift, probability_flow_score_drift, perturb_ve

def test_sigma_endpoints():
    assert abs(ve_sigma(0.0) - 0.01) < 1e-12
    assert abs(ve_sigma(1.0) - 50.0) < 1e-9

def test_probability_flow_half_reverse():
    reverse = reverse_score_drift(0.25, -0.7)
    flow = probability_flow_score_drift(0.25, -0.7)
    assert abs(2 * flow - reverse) < 1e-9

def test_perturb_target_sign():
    item = perturb_ve(1.0, 0.5, 0.4)
    assert item["xt"] > 1.0
    assert item["target_score"] < 0
