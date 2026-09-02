from atomic_loss import one_step, normal_logpdf

def test_one_step_reduces_loss():
    atoms=[-1.0,0.4,1.5]; obs=0.5
    prior=[normal_logpdf(a,0,1) for a in atoms]
    proposal=[normal_logpdf(a,0.4,0.7) for a in atoms]
    out=one_step(atoms, obs, 1, {'w':0.1,'b':0.0}, prior, proposal, lr=0.5)
    assert out['loss_after'] < out['loss_before']
    assert out['params_before'] != out['params_after']

from atomic_loss import learning_rate_sweep

def test_learning_rate_sweep_records_losses():
    atoms=[-1.0,0.4,1.5]; obs=0.5
    prior=[normal_logpdf(a,0,1) for a in atoms]
    proposal=[normal_logpdf(a,0.4,0.7) for a in atoms]
    out=learning_rate_sweep(atoms, obs, 1, {'w':0.1,'b':0.0}, prior, proposal, [0.1,0.5])
    assert len(out) == 2
    assert all(item['loss_after'] < item['loss_before'] for item in out)
