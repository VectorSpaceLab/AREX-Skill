from kde_update import gaussian_kde_density, pmd_weight_update, run_pmd_loop


def test_weight_update_normalizes_and_changes_ess():
    result = pmd_weight_update([0.5, 0.5], [0.0, 2.0], gamma=0.3)
    assert abs(sum(result["weights"]) - 1.0) < 1e-12
    assert result["weights"][1] > result["weights"][0]
    assert result["effective_sample_size"] <= 2.0


def test_pmd_loop_runs_with_callbacks():
    particles = [[-1.0, 1.0], [1.0, -1.0], [0.5, -0.5], [-0.5, 0.5]]
    observations = [0.0, 0.5, -0.5, 1.0]
    def log_likelihood(theta, observation):
        return -0.5 * (observation - theta[0]) ** 2
    def log_prior(theta):
        return -0.5 * (theta[0] ** 2 + theta[1] ** 2)
    result = run_pmd_loop(particles, observations, log_likelihood, log_prior, iterations=3, batch_size=2, seed=5)
    assert len(result["trace"]) == 3
    assert abs(sum(result["weights"]) - 1.0) < 1e-12
    assert gaussian_kde_density([0.0, 0.0], result["particles"], result["weights"], 0.5) > 0.0
