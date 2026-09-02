from recovery_harness import gaussian_posterior, median_mmd2


def test_gaussian_posterior_contract_shapes():
    observations = [[1.0, 0.0], [0.5, 0.2]]
    mean, cov_diag = gaussian_posterior(1.0, [1.0, 2.0], observations)
    assert len(mean) == 2
    assert len(cov_diag) == 2
    assert cov_diag[0] < 1.0


def test_mmd2_is_small_for_identical_samples():
    x = [[0.0], [1.0], [2.0]]
    value = median_mmd2(x, [row[:] for row in x])
    assert abs(value) < 1e-12
