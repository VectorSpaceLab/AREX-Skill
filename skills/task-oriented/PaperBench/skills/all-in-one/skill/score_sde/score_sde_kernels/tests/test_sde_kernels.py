from sde_kernels import SDEKernel, as_vector, perturb


def test_vp_and_subvp_marginal_bounds():
    vp = SDEKernel("vp", beta_min=0.1, beta_max=2.0)
    subvp = SDEKernel("subvp", beta_min=0.1, beta_max=2.0)
    _, vp_zero = vp.marginal_prob(1.0, 0.0)
    _, vp_std = vp.marginal_prob(1.0, 0.6)
    _, subvp_std = subvp.marginal_prob(1.0, 0.6)
    assert vp_zero == 0.0
    assert 0.0 < subvp_std <= vp_std < 1.0


def test_probability_flow_uses_half_score_correction():
    kernel = SDEKernel("vp", beta_min=0.1, beta_max=1.0)
    score = lambda x, t: [-0.5 * item for item in x]
    drift_raw, diffusion = kernel.sde([2.0], 0.5)
    reverse = as_vector(kernel.reverse_drift([2.0], 0.5, score, probability_flow=False))[0]
    ode = as_vector(kernel.reverse_drift([2.0], 0.5, score, probability_flow=True))[0]
    forward = as_vector(drift_raw)[0]
    assert abs((reverse - forward) - 2.0 * (ode - forward)) < 1e-12
    assert diffusion > 0.0


def test_ve_prior_and_perturbation_are_finite():
    kernel = SDEKernel("ve", sigma_min=0.01, sigma_max=2.0)
    sample = kernel.prior_sample(3, seed=7)
    logp = kernel.prior_logp(sample)
    perturbed = as_vector(perturb(kernel, [1.0, -1.0], 0.5, [0.0, 1.0]))
    assert len(sample) == 3
    assert logp < 0.0
    assert perturbed[0] == 1.0
    assert perturbed[1] > -1.0


def test_vp_std_monotonic_and_subvp_bounded_grid():
    vp = SDEKernel("vp", beta_min=0.1, beta_max=2.0)
    subvp = SDEKernel("subvp", beta_min=0.1, beta_max=2.0)
    previous = 0.0
    for t in [0.05, 0.2, 0.4, 0.7, 0.95]:
        _, vp_std = vp.marginal_prob(1.0, t)
        _, subvp_std = subvp.marginal_prob(1.0, t)
        assert vp_std >= previous
        assert 0.0 <= subvp_std <= vp_std
        previous = vp_std
