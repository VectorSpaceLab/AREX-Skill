from ddpm_utils import linear_beta_schedule, coefficients, posterior_mean_variance

def test_t0_posterior_variance_is_zero():
    row=coefficients(linear_beta_schedule(0.1, 0.2, 3))[0]
    post=posterior_mean_variance(0.25, 0.3, row)
    assert post['variance'] == 0.0
