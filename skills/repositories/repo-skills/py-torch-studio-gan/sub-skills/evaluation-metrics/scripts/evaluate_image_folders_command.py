#!/usr/bin/env python3
"""Build a safe StudioGAN standalone image-folder evaluation command.

This helper validates paths and metric/cache combinations, then prints the
command a user may run manually. It does not import StudioGAN, execute metrics,
download weights, train, or write output files.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

VALID_METRICS = {"is", "fid", "prdc"}
VALID_RESIZERS = {"legacy", "clean", "friendly"}
VALID_BACKBONES = {
    "InceptionV3_tf",
    "InceptionV3_torch",
    "ResNet50_torch",
    "SwAV_torch",
    "DINO_torch",
    "Swin-T_torch",
}


def existing_path_arg(value: str) -> Path:
    return Path(value).expanduser()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a StudioGAN src/evaluate.py command after validating metric input combinations."
    )
    parser.add_argument("--repo-root", required=True, type=existing_path_arg,
                        help="Path to a StudioGAN checkout containing src/evaluate.py.")
    parser.add_argument("--dset1", type=existing_path_arg, default=None,
                        help="Real/reference ImageFolder root. Required unless selected caches cover the metrics.")
    parser.add_argument("--dset2", required=True, type=existing_path_arg,
                        help="Generated/target ImageFolder root.")
    parser.add_argument("--metrics", nargs="+", default=["fid"],
                        help="Metrics to request: is fid prdc. Default: fid.")
    parser.add_argument("--dset1-feats", type=existing_path_arg, default=None,
                        help="Reference feature .npz cache with key real_feats, for PRDC without --dset1.")
    parser.add_argument("--dset1-moments", type=existing_path_arg, default=None,
                        help="Reference moment .npz cache with keys mu and sigma, for FID without --dset1.")
    parser.add_argument("--post-resizer", default="legacy", choices=sorted(VALID_RESIZERS),
                        help="StudioGAN post-resizer protocol. Default: legacy.")
    parser.add_argument("--eval-backbone", default="InceptionV3_tf", choices=sorted(VALID_BACKBONES),
                        help="StudioGAN evaluation backbone. Default: InceptionV3_tf.")
    parser.add_argument("--batch-size", type=int, default=256,
                        help="Evaluation batch size before DDP splitting. Default: 256.")
    parser.add_argument("--gpus", default="0",
                        help="CUDA_VISIBLE_DEVICES value to prepend to the command. Default: 0.")
    parser.add_argument("--ddp", action="store_true",
                        help="Include -DDP for StudioGAN distributed evaluation. Set MASTER_ADDR/MASTER_PORT before running.")
    return parser.parse_args()


def validate(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    repo_root = args.repo_root
    evaluate_py = repo_root / "src" / "evaluate.py"
    if not repo_root.exists() or not repo_root.is_dir():
        errors.append(f"--repo-root is not a directory: {repo_root}")
    elif not evaluate_py.is_file():
        errors.append(f"--repo-root does not contain src/evaluate.py: {repo_root}")

    metrics = [m.lower() for m in args.metrics]
    invalid_metrics = sorted(set(metrics) - VALID_METRICS)
    if invalid_metrics:
        errors.append("unsupported metrics: " + ", ".join(invalid_metrics) + " (expected is, fid, prdc)")
    args.metrics = metrics

    if args.batch_size <= 0:
        errors.append("--batch-size must be positive")

    if not args.dset2.exists() or not args.dset2.is_dir():
        errors.append(f"--dset2 must be an existing ImageFolder root: {args.dset2}")

    if args.dset1 is not None and (not args.dset1.exists() or not args.dset1.is_dir()):
        errors.append(f"--dset1 must be an existing ImageFolder root when supplied: {args.dset1}")

    if args.dset1_feats is not None:
        if not args.dset1_feats.is_file():
            errors.append(f"--dset1-feats must be an existing .npz file: {args.dset1_feats}")
        elif args.dset1_feats.suffix.lower() != ".npz":
            errors.append(f"--dset1-feats should be a StudioGAN .npz cache with key real_feats: {args.dset1_feats}")

    if args.dset1_moments is not None:
        if not args.dset1_moments.is_file():
            errors.append(f"--dset1-moments must be an existing .npz file: {args.dset1_moments}")
        elif args.dset1_moments.suffix.lower() != ".npz":
            errors.append(f"--dset1-moments should be a StudioGAN .npz cache with keys mu and sigma: {args.dset1_moments}")

    has_dset1 = args.dset1 is not None
    has_feats = args.dset1_feats is not None
    has_moments = args.dset1_moments is not None

    if not has_dset1 and not has_feats and not has_moments:
        errors.append("StudioGAN asserts --dset1 is required when neither --dset1-feats nor --dset1-moments is supplied")
    if "fid" in metrics and not (has_dset1 or has_moments):
        errors.append("FID requires --dset1 or --dset1-moments")
    if "prdc" in metrics and not (has_dset1 or has_feats):
        errors.append("PRDC requires --dset1 or --dset1-feats")

    if args.ddp:
        gpu_count = len([g for g in args.gpus.split(",") if g.strip()])
        if gpu_count <= 1:
            errors.append("--ddp was requested but --gpus lists fewer than two devices")
        if gpu_count > 0 and args.batch_size % gpu_count != 0:
            errors.append("--batch-size should be divisible by the number of visible GPUs for DDP")

    return errors


def quote_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(p)) for p in parts)


def main() -> int:
    args = parse_args()
    errors = validate(args)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    evaluate_py = args.repo_root / "src" / "evaluate.py"
    command = [
        "python",
        str(evaluate_py),
        "-metrics",
        *args.metrics,
        "--post_resizer",
        args.post_resizer,
        "--eval_backbone",
        args.eval_backbone,
        "--dset2",
        str(args.dset2),
        "--batch_size",
        str(args.batch_size),
    ]
    if args.dset1 is not None:
        command.extend(["--dset1", str(args.dset1)])
    if args.dset1_feats is not None:
        command.extend(["--dset1_feats", str(args.dset1_feats)])
    if args.dset1_moments is not None:
        command.extend(["--dset1_moments", str(args.dset1_moments)])
    if args.ddp:
        command.append("-DDP")

    print(f"CUDA_VISIBLE_DEVICES={shlex.quote(args.gpus)} {quote_command(command)}")
    if args.ddp:
        print("# Before running DDP, set MASTER_ADDR and MASTER_PORT in the shell.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
