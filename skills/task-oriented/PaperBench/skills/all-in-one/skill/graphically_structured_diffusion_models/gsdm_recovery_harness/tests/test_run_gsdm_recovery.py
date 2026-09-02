import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mixed_variable_diffusion_objective" / "scripts"))

from run_gsdm_recovery import deterministic_bcmf_item, train_scalar_step, variable_specs_and_values
from diffusion_objective import diffuse_x0, encode_values, observation_mask


def test_scalar_training_step_decreases_loss_and_changes_params():
    item = deterministic_bcmf_item()
    specs, values, observed = variable_specs_and_values(item)
    x0 = encode_values(specs, values)
    obs_mask = observation_mask(specs, observed)
    noise = [0.01 for _ in x0]
    xt = diffuse_x0(x0, noise, [0.001], 0)
    trace = train_scalar_step(__import__("diffusion_objective"), x0, xt, obs_mask, lr=0.05)
    assert trace["loss_after"] < trace["loss_before"]
    assert trace["params_after"] != trace["params_before"]
    assert trace["latent_dimension_count"] > 0


def test_scalar_training_step_still_decreases_with_small_lr():
    item = deterministic_bcmf_item()
    specs, values, observed = variable_specs_and_values(item)
    x0 = encode_values(specs, values)
    obs_mask = observation_mask(specs, observed)
    xt = diffuse_x0(x0, [0.01 for _ in x0], [0.001], 0)
    trace = train_scalar_step(__import__("diffusion_objective"), x0, xt, obs_mask, lr=0.01)
    assert trace["loss_after"] < trace["loss_before"]
