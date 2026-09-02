#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path


def _add_skill_paths(skills_root: str) -> None:
    for name in ["ddpm_adaptation_protocol", "pairwise_similarity_preservation", "haar_high_frequency_enhancement"]:
        path = Path(skills_root) / name / "scripts"
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


def _nested_map(a, fn):
    if isinstance(a, list):
        return [_nested_map(x, fn) for x in a]
    return fn(float(a))


def _nested_zip(a, b, fn):
    if isinstance(a, list):
        return [_nested_zip(x, y, fn) for x, y in zip(a, b)]
    return fn(float(a), float(b))


def _mse(a, b):
    vals = []
    def collect(x, y):
        vals.append((x - y) ** 2)
        return 0.0
    _nested_zip(a, b, collect)
    return sum(vals) / len(vals)


def target_batch():
    return [
        [[[1.0, -1.0], [-0.5, 0.75]]],
        [[[0.25, 0.9], [-0.8, -0.2]]],
        [[[-0.6, 0.4], [0.95, -0.95]]],
    ]


def noise_batch():
    return [
        [[[0.2, -0.1], [0.05, 0.3]]],
        [[[-0.15, 0.25], [0.1, -0.05]]],
        [[[0.05, 0.15], [-0.2, 0.35]]],
    ]


def source_epsilon(clean, noise):
    return _nested_zip(clean, noise, lambda x, n: 0.18 * x + 0.42 * n)


def adapted_epsilon(clean, noise, params):
    scale, bias = params
    return _nested_zip(clean, noise, lambda x, n: scale * x + 0.42 * n + bias)


def compute_loss(params, skills_root, weights):
    _add_skill_paths(skills_root)
    from ddpm_protocol import build_protocol
    from haar_hf import high_frequency_losses
    from pairwise_loss import pairwise_kl_loss

    clean = target_batch()
    noise = noise_batch()
    src_eps = source_epsilon(clean, noise)
    ada_eps = adapted_epsilon(clean, noise, params)
    protocol = build_protocol(clean, noise, src_eps, ada_eps, 0.72)
    image_pairwise = pairwise_kl_loss(protocol["source_x0_hat"], protocol["adapted_x0_hat"])["loss"]
    hf = high_frequency_losses(protocol["source_x0_hat"], protocol["adapted_x0_hat"], clean)
    simple = _mse(protocol["adapted_x0_hat"], clean)
    combined = simple + weights["lambda2"] * image_pairwise + weights["lambda3"] * hf["Lhf"] + weights["lambda4"] * hf["Lhfmse"]
    return combined, {
        "Lsimple_proxy": simple,
        "Limg": image_pairwise,
        "Lhf": hf["Lhf"],
        "Lhfmse": hf["Lhfmse"],
        "combined": combined,
        "protocol_metadata": protocol["metadata"],
        "hf_energy": hf["energy"],
    }


def finite_difference_step(params, skills_root, weights, lr=0.25, delta=1e-4):
    before_loss, before_components = compute_loss(params, skills_root, weights)
    grads = []
    for i in range(len(params)):
        plus = list(params)
        minus = list(params)
        plus[i] += delta
        minus[i] -= delta
        loss_plus, _ = compute_loss(plus, skills_root, weights)
        loss_minus, _ = compute_loss(minus, skills_root, weights)
        grads.append((loss_plus - loss_minus) / (2.0 * delta))
    after_params = [p - lr * g for p, g in zip(params, grads)]
    after_loss, after_components = compute_loss(after_params, skills_root, weights)
    return {
        "params_before": params,
        "params_after": after_params,
        "gradients": grads,
        "learning_rate": lr,
        "loss_before": before_loss,
        "loss_after": after_loss,
        "loss_delta": before_loss - after_loss,
        "components_before": before_components,
        "components_after": after_components,
    }


def run_proxy(skills_root, lambda2=0.5, lambda3=0.5, lambda4=0.04, learning_rate=0.25):
    weights = {"lambda2": lambda2, "lambda3": lambda3, "lambda4": lambda4}
    trace = finite_difference_step([0.62, 0.08], skills_root, weights, lr=learning_rate)
    changed = any(abs(a - b) > 1e-10 for a, b in zip(trace["params_before"], trace["params_after"]))
    finite = all(math.isfinite(v) for v in [trace["loss_before"], trace["loss_after"], trace["loss_delta"]])
    return {
        "trace": trace,
        "metric": {"combined_loss_delta": trace["loss_delta"]},
        "mechanism_checks": {
            "proxy_declared": True,
            "full_pretrained_ddpm_loaded": False,
            "shared_noised_batch_constructed": True,
            "x0_reconstruction_executed": True,
            "image_pairwise_kl_executed": True,
            "haar_high_frequency_executed": True,
            "high_frequency_pairwise_kl_executed": True,
            "high_frequency_mse_executed": True,
            "reduced_training_executed": True,
            "optimizer_step_executed": changed,
            "finite_losses": finite,
            "loss_decreased": trace["loss_after"] < trace["loss_before"],
        },
        "weights": weights,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skills-root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--output", required=True)
    parser.add_argument("--lambda2", type=float, default=0.5)
    parser.add_argument("--lambda3", type=float, default=0.5)
    parser.add_argument("--lambda4", type=float, default=0.04)
    parser.add_argument("--learning-rate", type=float, default=0.25)
    args = parser.parse_args()
    result = run_proxy(args.skills_root, args.lambda2, args.lambda3, args.lambda4, args.learning_rate)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "output": args.output, "loss_delta": result["metric"]["combined_loss_delta"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
