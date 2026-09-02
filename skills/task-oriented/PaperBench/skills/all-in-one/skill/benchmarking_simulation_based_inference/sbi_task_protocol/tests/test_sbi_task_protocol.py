from sbi_task_protocol import (
    gaussian_linear_reference_posterior,
    normalize_task,
    sample_reference,
    simulate,
)


def test_gaussian_linear_reference_posterior_shrinks_variance():
    task = normalize_task(
        task_name="tiny",
        dim_parameters=1,
        dim_data=1,
        prior_mean=[0.0],
        prior_variance=1.0,
        simulator_variance=0.25,
        observation=[0.4],
        num_simulations=5,
    )
    posterior = gaussian_linear_reference_posterior(task)
    assert posterior["variance"] < task["prior"]["variance"]
    assert abs(posterior["mean"][0] - 0.32) < 1e-9


def test_simulation_and_reference_sample_counts():
    task = normalize_task("tiny", 1, 1, [0.0], 1.0, 0.25, [0.4], 5)
    simulations = simulate(task, seed=1, num_samples=7)
    reference = sample_reference(task, seed=2, num_samples=9)
    assert len(simulations["theta"]) == 7
    assert len(simulations["x"]) == 7
    assert len(reference["samples"]) == 9
