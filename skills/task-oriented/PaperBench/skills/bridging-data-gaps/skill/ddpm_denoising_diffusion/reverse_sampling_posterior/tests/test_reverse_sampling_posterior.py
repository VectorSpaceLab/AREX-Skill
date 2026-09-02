from ddpm_utils import linear_beta_schedule, coefficients, q_sample_scalar, predict_start_from_noise, posterior_mean_variance

def test_perfect_epsilon_reconstructs_xstart():
    row=coefficients(linear_beta_schedule(0.1,0.2,3))[1]
    xt=q_sample_scalar(0.7,-0.4,row)
    x0=predict_start_from_noise(xt,-0.4,row)
    post=posterior_mean_variance(x0,xt,row)
    assert abs(x0-0.7) < 1e-12
    assert post['variance'] > 0
