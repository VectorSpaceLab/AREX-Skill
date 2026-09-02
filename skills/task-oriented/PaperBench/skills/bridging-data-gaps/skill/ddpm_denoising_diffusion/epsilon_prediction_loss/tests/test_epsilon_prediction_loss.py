from ddpm_utils import mse_loss, gradient_step

def test_gradient_step_reduces_loss():
    samples=[{'x_t':0.2,'t_scaled':0.0,'epsilon':0.5},{'x_t':-0.1,'t_scaled':1.0,'epsilon':-0.3}]
    theta=[0.0,0.0,0.0]
    before=mse_loss(samples,theta)
    after_theta=gradient_step(samples,theta,0.2)
    after=mse_loss(samples,after_theta)
    assert after < before
    assert after_theta != theta
