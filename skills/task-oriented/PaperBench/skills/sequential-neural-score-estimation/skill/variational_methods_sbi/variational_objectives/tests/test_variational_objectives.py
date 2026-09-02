from objectives import normalized_weights, fkl_surrogate

def test_weights_are_stable():
    ws=normalized_weights([-1000,-999])
    assert abs(sum(ws)-1.0)<1e-12
    assert ws[1]>ws[0]

def test_fkl_returns_diagnostics():
    loss,ws,ess=fkl_surrogate([-1.0,-2.0],[-1.5,-1.5])
    assert isinstance(loss,float)
    assert len(ws)==2
    assert ess>=1.0


def test_effective_sample_size_prefers_balanced_weights():
    from objectives import effective_sample_size
    assert effective_sample_size([0.5,0.5]) > effective_sample_size([0.9,0.1])
