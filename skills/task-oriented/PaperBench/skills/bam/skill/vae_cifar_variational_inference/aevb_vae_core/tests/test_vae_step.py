#!/usr/bin/env python3
"""Smoke tests for the compact VAE step."""

from pathlib import Path
import importlib.util
import math

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("run_vae_step", ROOT / "scripts" / "run_vae_step.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

batch = {
    "images": [
        [[[1.0, 0.0], [0.0, 1.0]]],
        [[[0.0, 1.0], [1.0, 0.0]]],
    ]
}
trace = module.run_step(batch, latent_dim=2, learning_rate=0.01, seed=0)
assert trace["sample_count"] == 2
assert trace["input_dim"] == 4
assert math.isfinite(trace["reconstruction_loss_before"])
assert math.isfinite(trace["kl_loss_before"])
assert math.isfinite(trace["total_loss_before"])
assert trace["kl_loss_before"] >= -1e-6
assert trace["params_before"] != trace["params_after"]
checks = trace["mechanism_checks"]
for key in ["encoder_executed", "reparameterization_executed", "decoder_executed", "reconstruction_loss_computed", "kl_divergence_computed", "optimizer_step_executed", "reduced_training_executed"]:
    assert checks[key] is True
assert checks["full_training_executed"] is False
