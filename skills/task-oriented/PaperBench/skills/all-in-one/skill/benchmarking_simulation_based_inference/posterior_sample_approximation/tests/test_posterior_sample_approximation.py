from posterior_sample_approximation import fit_affine_posterior


def test_affine_training_reduces_loss_and_changes_params():
    simulations = {"theta": [], "x": []}
    for i in range(-10, 11):
        x = [i / 10.0]
        simulations["x"].append(x)
        simulations["theta"].append([0.7 * x[0] + 0.2])
    result = fit_affine_posterior(
        simulations=simulations,
        observation=[0.25],
        learning_rate=0.08,
        steps=90,
        sample_count=12,
        sample_variance=0.03,
        seed=11,
    )
    trace = result["trace"]
    assert trace["loss_after"] < trace["loss_before"]
    assert trace["params_before"] != trace["params_after"]
    assert len(result["samples"]) == 12


def test_zero_step_training_does_not_claim_optimizer_change():
    simulations = {"theta": [[-0.3], [0.0], [0.3]], "x": [[-0.4], [0.0], [0.4]]}
    result = fit_affine_posterior(
        simulations=simulations,
        observation=[0.1],
        learning_rate=0.1,
        steps=0,
        sample_count=5,
        sample_variance=0.02,
        seed=13,
    )
    trace = result["trace"]
    assert trace["optimizer_state_changed"] is False
    assert trace["params_before"] == trace["params_after"]
    assert trace["loss_before"] == trace["loss_after"]
