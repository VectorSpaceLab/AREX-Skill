from sequential_proxy import run_proxy

def test_proxy_updates_proposal_and_trains():
    out=run_proxy()
    assert out['sample_count'] == 64
    assert out['posterior_mean_abs_error'] < abs(out['analytic_posterior_mean'])
    assert out['training_trace']['params_before'] != out['training_trace']['params_after']

def test_proxy_supports_stress_parameters():
    out=run_proxy(obs=0.9, rounds=3, simulations_per_round=16, proposal_scale=1.2)
    assert out['sample_count'] == 48
    assert out['posterior_mean_abs_error'] < 0.35
