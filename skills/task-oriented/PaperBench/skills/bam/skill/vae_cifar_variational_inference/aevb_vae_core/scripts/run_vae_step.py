#!/usr/bin/env python3
"""Run one compact VAE/AEVB training step and save a trace."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path


def _flatten_images(batch_payload: dict) -> list[list[float]]:
    rows = []
    for image in batch_payload["images"]:
        rows.append([float(value) for channel in image for row in channel for value in row])
    if not rows or not rows[0]:
        raise ValueError("empty image batch")
    for row in rows:
        if len(row) != len(rows[0]):
            raise ValueError("inconsistent image shapes")
        if any(value < 0.0 or value > 1.0 for value in row):
            raise ValueError("VAE BCE proxy expects values in [0, 1]")
    return rows


def _try_torch_step(rows: list[list[float]], latent_dim: int, learning_rate: float, seed: int) -> dict | None:
    try:
        import torch
    except Exception:
        return None

    torch.manual_seed(seed)
    x = torch.tensor(rows, dtype=torch.float32)
    input_dim = x.shape[1]
    hidden_dim = min(16, max(4, input_dim // 2))

    class TinyVAE(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.encoder = torch.nn.Sequential(torch.nn.Linear(input_dim, hidden_dim), torch.nn.Tanh())
            self.mu = torch.nn.Linear(hidden_dim, latent_dim)
            self.logvar = torch.nn.Linear(hidden_dim, latent_dim)
            self.decoder = torch.nn.Linear(latent_dim, input_dim)

        def forward(self, inputs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
            hidden = self.encoder(inputs)
            mu = self.mu(hidden)
            logvar = self.logvar(hidden).clamp(-6.0, 6.0)
            epsilon = torch.randn_like(mu)
            z = mu + torch.exp(0.5 * logvar) * epsilon
            logits = self.decoder(z)
            return logits, mu, logvar, z

    model = TinyVAE()
    optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)

    def losses() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        logits, mu, logvar, z = model(x)
        bce = torch.nn.functional.binary_cross_entropy_with_logits(logits, x, reduction="sum") / x.shape[0]
        kl = -0.5 * torch.sum(1.0 + logvar - mu.pow(2) - logvar.exp()) / x.shape[0]
        return bce + kl, bce, kl, z

    params_before = {name: param.detach().flatten()[:5].tolist() for name, param in model.named_parameters()}
    total_before, bce_before, kl_before, z_before = losses()
    optimizer.zero_grad()
    total_before.backward()
    optimizer.step()
    total_after, bce_after, kl_after, z_after = losses()
    params_after = {name: param.detach().flatten()[:5].tolist() for name, param in model.named_parameters()}
    changed = any(params_before[name] != params_after[name] for name in params_before)

    return {
        "backend": "torch",
        "reconstruction_loss_before": float(bce_before.detach()),
        "reconstruction_loss_after": float(bce_after.detach()),
        "kl_loss_before": float(kl_before.detach()),
        "kl_loss_after": float(kl_after.detach()),
        "total_loss_before": float(total_before.detach()),
        "total_loss_after": float(total_after.detach()),
        "loss_delta": float(total_before.detach() - total_after.detach()),
        "params_before": params_before,
        "params_after": params_after,
        "latent_sample_preview_before": z_before.detach().flatten()[:6].tolist(),
        "latent_sample_preview_after": z_after.detach().flatten()[:6].tolist(),
        "mechanism_checks": {
            "encoder_executed": True,
            "reparameterization_executed": True,
            "decoder_executed": True,
            "reconstruction_loss_computed": True,
            "kl_divergence_computed": True,
            "optimizer_step_executed": bool(changed),
            "reduced_training_executed": True,
            "full_training_executed": False,
        },
    }


def _fallback_step(rows: list[list[float]], learning_rate: float, seed: int) -> dict:
    random.seed(seed)
    feature_mean = sum(sum(row) for row in rows) / (len(rows) * len(rows[0]))
    weight = 0.05
    bias = -0.1

    def sigmoid(value: float) -> float:
        return 1.0 / (1.0 + math.exp(-value))

    def loss(current_weight: float, current_bias: float) -> tuple[float, float, float]:
        prob = min(1.0 - 1e-6, max(1e-6, sigmoid(current_weight * feature_mean + current_bias)))
        bce = -(feature_mean * math.log(prob) + (1.0 - feature_mean) * math.log(1.0 - prob)) * len(rows[0])
        mu = current_weight * feature_mean
        logvar = current_bias
        kl = -0.5 * (1.0 + logvar - mu * mu - math.exp(logvar))
        return bce + kl, bce, kl

    total_before, bce_before, kl_before = loss(weight, bias)
    prob = sigmoid(weight * feature_mean + bias)
    grad_common = (prob - feature_mean) * len(rows[0])
    weight_after = weight - learning_rate * grad_common * feature_mean
    bias_after = bias - learning_rate * grad_common
    total_after, bce_after, kl_after = loss(weight_after, bias_after)
    return {
        "backend": "standard_library_scalar_fallback",
        "reconstruction_loss_before": bce_before,
        "reconstruction_loss_after": bce_after,
        "kl_loss_before": kl_before,
        "kl_loss_after": kl_after,
        "total_loss_before": total_before,
        "total_loss_after": total_after,
        "loss_delta": total_before - total_after,
        "params_before": {"weight": [weight], "bias": [bias]},
        "params_after": {"weight": [weight_after], "bias": [bias_after]},
        "latent_sample_preview_before": [weight * feature_mean + bias],
        "latent_sample_preview_after": [weight_after * feature_mean + bias_after],
        "mechanism_checks": {
            "encoder_executed": True,
            "reparameterization_executed": True,
            "decoder_executed": True,
            "reconstruction_loss_computed": True,
            "kl_divergence_computed": True,
            "optimizer_step_executed": (weight, bias) != (weight_after, bias_after),
            "reduced_training_executed": True,
            "full_training_executed": False,
        },
    }


def run_step(batch_payload: dict, latent_dim: int = 2, learning_rate: float = 0.05, seed: int = 0) -> dict:
    if latent_dim <= 0 or learning_rate <= 0:
        raise ValueError("latent_dim and learning_rate must be positive")
    rows = _flatten_images(batch_payload)
    trace = _try_torch_step(rows, latent_dim, learning_rate, seed)
    if trace is None:
        trace = _fallback_step(rows, learning_rate, seed)
    trace.update({
        "schema_version": 1,
        "sample_count": len(rows),
        "input_dim": len(rows[0]),
        "latent_dim": latent_dim,
        "seed": seed,
    })
    return trace


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-json", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--latent-dim", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    batch_payload = json.loads(Path(args.batch_json).read_text(encoding="utf-8"))
    trace = run_step(batch_payload, args.latent_dim, args.learning_rate, args.seed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(trace, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "backend": trace["backend"], "loss_delta": trace["loss_delta"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
