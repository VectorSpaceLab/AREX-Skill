#!/usr/bin/env python3
"""Validate common PyTorch DPM-Solver option combinations without loading models."""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-type", choices=["dpmsolver", "dpmsolver++"], required=True)
    parser.add_argument("--steps", type=int, required=True)
    parser.add_argument("--order", type=int, choices=[1, 2, 3], required=True)
    parser.add_argument("--method", choices=["adaptive", "singlestep", "multistep", "singlestep_fixed"], required=True)
    parser.add_argument("--skip-type", choices=["logSNR", "time_uniform", "time_quadratic"], required=True)
    parser.add_argument("--solver-type", choices=["dpmsolver", "taylor"], default="dpmsolver")
    parser.add_argument("--guided", action="store_true", help="large classifier/classifier-free guidance is expected")
    parser.add_argument("--thresholding", action="store_true")
    parser.add_argument("--latent", action="store_true", help="sample space is latent, e.g. Stable Diffusion")
    args = parser.parse_args()

    warnings: list[str] = []
    errors: list[str] = []

    if args.method == "multistep" and args.steps < args.order:
        errors.append("multistep requires steps >= order")
    if args.method == "adaptive" and args.steps:
        warnings.append("adaptive ignores the fixed steps count and uses atol/rtol")
    if args.guided and args.order != 2:
        warnings.append("large-guidance workflows usually use order=2")
    if args.guided and args.sample_type != "dpmsolver++":
        warnings.append("large-guidance workflows usually use dpmsolver++")
    if args.latent and args.thresholding:
        errors.append("dynamic thresholding is not suitable for latent-space samples")
    if args.thresholding and args.sample_type != "dpmsolver++":
        warnings.append("thresholding is designed for the DPM-Solver++ data-prediction path")
    if args.skip_type == "logSNR" and not args.guided:
        warnings.append("logSNR is common for low-resolution CIFAR-style examples; confirm this is not a high-resolution latent run")
    if args.skip_type == "time_uniform" and not args.guided:
        warnings.append("time_uniform is common for high-resolution or latent tasks; compare logSNR for CIFAR-like tasks")

    for item in warnings:
        print(f"WARNING: {item}")
    for item in errors:
        print(f"ERROR: {item}")
    if errors:
        return 2
    print("Option combination is structurally valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
