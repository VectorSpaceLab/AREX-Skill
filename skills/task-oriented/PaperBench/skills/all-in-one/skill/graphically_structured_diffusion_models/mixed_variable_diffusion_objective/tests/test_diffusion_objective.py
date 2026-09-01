import math

from diffusion_objective import (
    decode_values,
    diffuse_x0,
    encode_values,
    masked_mse,
    observation_mask,
)


def test_categorical_roundtrip_and_observation_mask():
    specs = [
        {"name": "x", "kind": "continuous"},
        {"name": "z", "kind": "categorical", "num_categories": 3},
    ]
    encoded = encode_values(specs, {"x": 0.5, "z": 2})
    assert encoded == [0.5, 0.0, 0.0, 1.0]
    assert decode_values(specs, encoded) == {"x": 0.5, "z": 2}
    assert observation_mask(specs, ["z"]) == [0, 1, 1, 1]


def test_diffuse_x0_matches_closed_form():
    x0 = [1.0, 0.0]
    noise = [0.0, 1.0]
    xt = diffuse_x0(x0, noise, [0.25], 0)
    assert abs(xt[0] - math.sqrt(0.75)) < 1e-12
    assert abs(xt[1] - math.sqrt(0.25)) < 1e-12


def test_masked_mse_uses_only_active_latents():
    assert masked_mse([0.0, 2.0, 10.0], [1.0, 0.0, 0.0], [1, 1, 0]) == 2.5


def test_observed_categorical_expands_all_one_hot_channels():
    specs = [
        {"name": "x", "kind": "continuous"},
        {"name": "z", "kind": "categorical", "num_categories": 4},
        {"name": "y", "kind": "continuous"},
    ]
    encoded = encode_values(specs, {"x": 0.2, "z": 3, "y": 0.8})
    obs_mask = observation_mask(specs, ["z"])
    latent_mask = [0 if flag else 1 for flag in obs_mask]
    assert len(encoded) == 6
    assert sum(obs_mask) == 4
    assert sum(latent_mask) == 2
    assert abs(masked_mse([0.0] * len(encoded), encoded, latent_mask) - 0.34) < 1e-12
