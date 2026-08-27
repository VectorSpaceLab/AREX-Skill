#!/usr/bin/env python3
"""Build safe command templates for DPM-Solver PyTorch examples.

The script prints commands only; it does not run downloads, load checkpoints, or
create output directories.
"""

from __future__ import annotations

import argparse
import shlex


def q(parts):
    return " ".join(shlex.quote(str(p)) for p in parts if p is not None)


def ddpm_command(args):
    parts = [
        "python", "main.py",
        "--config", args.config,
        "--exp", args.workdir,
        "--sample",
    ]
    if args.fid:
        parts.append("--fid")
    parts += [
        "--timesteps", args.steps,
        "--eta", "0",
        "--ni",
        "--skip_type", args.skip_type,
        "--sample_type", args.sample_type,
        "--dpm_solver_order", args.order,
        "--dpm_solver_method", args.method,
        "--dpm_solver_type", args.solver_type,
        "--port", args.port,
    ]
    if args.scale is not None:
        parts += ["--scale", args.scale]
    if args.thresholding:
        parts.append("--thresholding")
    if args.denoise:
        parts.append("--denoise")
    if args.lower_order_final:
        parts.append("--lower_order_final")
    return q(parts)


def scoresde_command(args):
    parts = [
        "python", "main.py",
        "--config", args.config,
        "--mode", "eval",
        "--workdir", args.workdir,
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
    return q(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="family", required=True)

    ddpm = sub.add_parser("ddpm-guided", help="DDPM/improved-DDPM/guided-diffusion example")
    ddpm.add_argument("--config", default="cifar10.yml")
    ddpm.add_argument("--workdir", default="experiments/cifar10_dpm_solver_plan")
    ddpm.add_argument("--steps", type=int, default=10)
    ddpm.add_argument("--skip-type", default="logSNR", choices=["logSNR", "time_uniform", "time_quadratic"])
    ddpm.add_argument("--sample-type", default="dpmsolver++", choices=["dpmsolver", "dpmsolver++"])
    ddpm.add_argument("--order", type=int, default=3, choices=[1, 2, 3])
    ddpm.add_argument("--method", default="multistep", choices=["adaptive", "singlestep", "multistep", "singlestep_fixed"])
    ddpm.add_argument("--solver-type", default="dpmsolver", choices=["dpmsolver", "taylor"])
    ddpm.add_argument("--scale", type=float)
    ddpm.add_argument("--thresholding", action="store_true")
    ddpm.add_argument("--denoise", action="store_true")
    ddpm.add_argument("--lower-order-final", action="store_true")
    ddpm.add_argument("--fid", action="store_true")
    ddpm.add_argument("--port", default="12355")

    ssde = sub.add_parser("score-sde", help="ScoreSDE PyTorch example")
    ssde.add_argument("--config", default="configs/vp/cifar10_ddpmpp_deep_continuous.py")
    ssde.add_argument("--workdir", default="experiments/cifar10_ddpmpp_deep_continuous_steps")
    ssde.add_argument("--steps", type=int, default=10)
    ssde.add_argument("--eps", default="1e-3")
    ssde.add_argument("--skip-type", default="logSNR", choices=["logSNR", "time_uniform", "time_quadratic"])
    ssde.add_argument("--order", type=int, default=3, choices=[1, 2, 3])
    ssde.add_argument("--method", default="singlestep", choices=["adaptive", "singlestep", "multistep", "singlestep_fixed"])
    ssde.add_argument("--batch-size", type=int, default=1000)
    ssde.add_argument("--denoise", action="store_true")

    args = parser.parse_args()
    if args.family == "ddpm-guided":
        print(ddpm_command(args))
    else:
        print(scoresde_command(args))
    print("# Review checkpoint, dataset, stats, GPU, and output-directory requirements before running.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
