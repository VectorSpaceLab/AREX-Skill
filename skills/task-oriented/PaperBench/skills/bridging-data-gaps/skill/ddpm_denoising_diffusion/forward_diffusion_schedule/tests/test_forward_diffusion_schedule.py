from ddpm_utils import linear_beta_schedule, coefficients, q_sample_scalar

def test_schedule_and_q_sample():
    betas=linear_beta_schedule(0.1,0.2,3)
    rows=coefficients(betas)
    assert betas == [0.1,0.15000000000000002,0.2]
    assert rows[1]['alpha_cumprod'] < rows[0]['alpha_cumprod']
    xt=q_sample_scalar(1.0,0.0,rows[0])
    assert abs(xt - rows[0]['sqrt_alpha_cumprod']) < 1e-12
