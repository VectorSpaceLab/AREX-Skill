#!/usr/bin/env python3
"""Build a Stable Diffusion txt2img DPM-Solver command template."""

from __future__ import annotations

import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", default="a photograph of an astronaut riding a horse")
    parser.add_argument("--outdir", default="outputs/txt2img-samples")
    parser.add_argument("--steps", type=int, default=25, help="passed to --ddim_steps in the legacy script")
    parser.add_argument("--scale", type=float, default=7.5)
    parser.add_argument("--n-samples", type=int, default=1)
    parser.add_argument("--n-iter", type=int, default=1)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--config", default="configs/stable-diffusion/v1-inference.yaml")
    parser.add_argument("--ckpt", default="models/ldm/stable-diffusion-v1/model.ckpt")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--precision", choices=["full", "autocast"], default="autocast")
    parser.add_argument("--skip-grid", action="store_true")
    parser.add_argument("--skip-save", action="store_true")
    parser.add_argument("--from-file")
    args = parser.parse_args()

    parts = [
        "python", "scripts/txt2img.py",
        "--prompt", args.prompt,
        "--outdir", args.outdir,
        "--dpm_solver",
        "--ddim_steps", args.steps,
        "--scale", args.scale,
        "--n_samples", args.n_samples,
        "--n_iter", args.n_iter,
        "--H", args.height,
        "--W", args.width,
        "--config", args.config,
        "--ckpt", args.ckpt,
        "--seed", args.seed,
        "--precision", args.precision,
    ]
    if args.skip_grid:
        parts.append("--skip_grid")
    if args.skip_save:
        parts.append("--skip_save")
    if args.from_file:
        parts += ["--from-file", args.from_file]

    print(" ".join(shlex.quote(str(part)) for part in parts))
    print("# Confirm checkpoint license/access, config match, CUDA memory, safety-checker/watermark dependencies, and output policy before running.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
