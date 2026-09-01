from langevin_sampler import gaussian_score, sample_gaussian


def test_gaussian_score_sign():
    assert gaussian_score(2.0, mean=1.0, variance=0.5) < 0
    assert gaussian_score(0.0, mean=1.0, variance=0.5) > 0


def test_sampler_runs_finite_score_updates():
    result = sample_gaussian(mean=0.5, variance=0.2, sample_count=16, seed=1, levels=3, steps_per_level=2, step_size=0.02)
    assert len(result["samples"]) == 16
    assert result["trace"]["score_evaluations"] == 96
    assert result["trace"]["all_finite"] is True
