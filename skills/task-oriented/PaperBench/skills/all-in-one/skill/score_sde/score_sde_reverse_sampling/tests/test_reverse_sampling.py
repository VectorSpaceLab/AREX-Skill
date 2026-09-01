from reverse_sampling import SamplerConfig, langevin_corrector_step, predictor_step, run_sampler


def test_probability_flow_predictor_is_deterministic_with_zero_diffusion():
    drift_fn = lambda x, t: [-0.5 * item for item in x]
    diffusion_fn = lambda t: 1.0
    score_fn = lambda x, t: [-item for item in x]
    import random

    a, _ = predictor_step([1.0], 0.5, -0.1, drift_fn, diffusion_fn, score_fn, random.Random(1), probability_flow=True)
    b, _ = predictor_step([1.0], 0.5, -0.1, drift_fn, diffusion_fn, score_fn, random.Random(999), probability_flow=True)
    assert a == b


def test_corrector_moves_in_score_direction_without_noise():
    score_fn = lambda x, t: [1.0 for _ in x]
    import random

    updated, diag = langevin_corrector_step([0.0], 0.5, score_fn, 0.1, random.Random(1), noise_scale=0.0)
    assert updated[0] == 0.1
    assert diag["score_norm"] == 1.0


def test_run_sampler_logs_trajectory_and_score_calls():
    drift_fn = lambda x, t: [0.0 for _ in x]
    diffusion_fn = lambda t: 0.1
    score_fn = lambda x, t: [-item for item in x]
    result = run_sampler([1.0], SamplerConfig(times=[1.0, 0.5], dt=-0.1, probability_flow=True), drift_fn, diffusion_fn, score_fn)
    assert len(result["trajectory"]) == 3
    assert result["score_evaluations"] == 2
    assert len(result["final_state"]) == 1
