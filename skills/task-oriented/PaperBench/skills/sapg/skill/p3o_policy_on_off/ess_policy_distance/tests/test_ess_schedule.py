from ess_schedule import compute_ess_schedule

def test_equal_policies_have_unit_ess():
    out = compute_ess_schedule([0.25, 0.75], [0.25, 0.75])
    assert abs(out['ess'] - 1.0) < 1e-12
    assert out['clip_threshold'] == out['ess']
    assert abs(out['kl_coefficient']) < 1e-12

def test_shifted_policies_are_bounded():
    out = compute_ess_schedule([0.95, 0.05], [0.5, 0.5])
    assert 0.0 <= out['ess'] <= 1.0
    assert abs(out['clip_threshold'] + out['kl_coefficient'] - 1.0) < 1e-12
