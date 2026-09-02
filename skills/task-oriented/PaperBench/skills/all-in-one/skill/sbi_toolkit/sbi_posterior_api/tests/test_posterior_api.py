from posterior_api import ScalarGaussianPosterior


def test_conditioning_changes_posterior_mean():
    posterior = ScalarGaussianPosterior(a=0.5, b=0.1, posterior_std=0.75)
    assert posterior.mean(0.0) == 0.1
    assert posterior.mean(2.0) == 1.1


def test_sampling_is_reproducible_and_log_prob_is_finite():
    posterior = ScalarGaussianPosterior(a=0.5, b=0.0, posterior_std=0.75)
    first = posterior.sample(1.0, 4, seed=123)
    second = posterior.sample(1.0, 4, seed=123)
    assert first == second
    assert posterior.log_prob(posterior.mean(1.0), 1.0) > -1.0
