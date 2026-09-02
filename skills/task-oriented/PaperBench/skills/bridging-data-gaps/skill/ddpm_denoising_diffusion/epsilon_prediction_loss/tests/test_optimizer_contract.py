from ddpm_utils import gradient_step, mse_loss

def test_zero_learning_rate_keeps_parameters_and_loss():
    samples=[{'x_t':0.4,'t_scaled':0.5,'epsilon':-0.2}]
    theta=[0.1, -0.3, 0.2]
    after=gradient_step(samples, theta, 0.0)
    assert after == theta
    assert mse_loss(samples, after) == mse_loss(samples, theta)
