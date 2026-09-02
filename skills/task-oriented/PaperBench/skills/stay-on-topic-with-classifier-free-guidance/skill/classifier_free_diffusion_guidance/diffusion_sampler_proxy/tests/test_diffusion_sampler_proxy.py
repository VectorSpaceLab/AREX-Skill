from sampler_proxy import sample_proxy

def test_guidance_moves_toward_class():
    base=sample_proxy([0.0], class_mean=2.0, global_mean=0.0, w=0.0, steps=4)['samples'][0]
    guided=sample_proxy([0.0], class_mean=2.0, global_mean=0.0, w=1.0, steps=4)['samples'][0]
    assert guided > base

def test_trace_has_dual_predictions():
    tr=sample_proxy([0.0],1.0,0.0,0.5,steps=1)['trace'][0]
    assert 'eps_cond' in tr and 'eps_uncond' in tr and 'eps_guided' in tr
