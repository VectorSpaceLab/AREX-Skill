#!/usr/bin/env python3
"""Print a JAX ScoreSDE DPM-Solver command template without running it."""

from __future__ import annotations

import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/vp/cifar10_ddpmpp_deep_continuous.py")
    parser.add_argument("--workdir", default="experiments/cifar10_ddpmpp_deep_continuous_steps")
    parser.add_argument("--mode", choices=["eval", "train"], default="eval")
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--eps", default="1e-3")
    parser.add_argument("--skip-type", choices=["logSNR", "time_uniform", "time_quadratic"], default="logSNR")
    parser.add_argument("--order", type=int, choices=[1, 2, 3], default=3)
    parser.add_argument("--method", choices=["adaptive", "singlestep", "multistep", "singlestep_fixed"], default="singlestep")
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--denoise", action="store_true")
    args = parser.parse_args()

    if args.method == "multistep" and args.steps < args.order:
        raise SystemExit("multistep requires --steps >= --order")

    parts = [
        "python", "main.py",
        "--config", args.config,
        "--mode", args.mode,
        "--workdir", args.workdir,
    ]
    if args.mode == "eval":
        parts += [
            f"--config.sampling.eps={args.eps}",
            "--config.sampling.method=dpm_solver",
            f"--config.sampling.steps={args.steps}",
            f"--config.sampling.skip_type={args.skip_type}",
            f"--config.sampling.dpm_solver_order={args.order}",
            f"--config.sampling.dpm_solver_method={args.method}",
            f"--config.eval.batch_size={args.batch_size}",
        ]
        if args.denoise:
            parts.append("--config.sampling.noise_removal=True")

    print(" ".join(shlex.quote(str(part)) for part in parts))
    print("# Confirm JAX/Flax/TensorFlow versions, checkpoint/data/stat files, and jax.devices() before running.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
