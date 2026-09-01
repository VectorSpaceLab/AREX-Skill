from sampler import refine

def test_refinement_moves_toward_target_prior():
    out = refine(initial_state=-0.5, condition=0.25, scale_factor=4.0, weight=0.3, steps=5)
    assert len(out['trajectory']) == 5
    assert abs(out['final'] - 1.0) < abs(-0.5 - 1.0)
