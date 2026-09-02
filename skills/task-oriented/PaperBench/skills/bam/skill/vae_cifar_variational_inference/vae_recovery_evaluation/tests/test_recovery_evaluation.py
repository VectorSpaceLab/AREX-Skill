#!/usr/bin/env python3
"""Smoke tests for VAE recovery result building."""

from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_recovery_result", ROOT / "scripts" / "build_recovery_result.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

plan = {
    "paper_id": "vae_cifar_variational_inference",
    "fast_recovery_target": {
        "dataset": "synthetic_binary_images",
        "split": "deterministic_tiny_batch_8x8",
        "metric": "loss_delta",
        "paper_value": 0.0,
        "proxy": True,
        "rationale": "bounded mechanism-faithful proxy",
    },
}
trace = {
    "sample_count": 2,
    "total_loss_before": 3.0,
    "total_loss_after": 2.7,
    "loss_delta": 0.3,
    "reconstruction_loss_before": 2.5,
    "reconstruction_loss_after": 2.2,
    "kl_loss_before": 0.5,
    "kl_loss_after": 0.5,
    "params_before": {"w": [0.0]},
    "params_after": {"w": [0.1]},
    "mechanism_checks": {
        "encoder_executed": True,
        "reparameterization_executed": True,
        "decoder_executed": True,
        "reconstruction_loss_computed": True,
        "kl_divergence_computed": True,
        "optimizer_step_executed": True,
    },
}
result = module.build_result(plan, trace, "python run.py", ["recovery/logs/training_trace.json"])
assert result["is_proxy"] is True
assert result["paper_target"]["dataset"] == "synthetic_binary_images"
assert result["paper_target"]["metric"] == "loss_delta"
assert result["metrics"]["loss_delta"] == 0.3
assert result["mechanism_checks"]["params_before_after_recorded"] is True
assert result["commands"] == ["python run.py"]
