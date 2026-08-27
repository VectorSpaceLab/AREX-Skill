#!/usr/bin/env python3
"""Build a safe gaussian-splatting train.py command.

The helper validates option combinations and prints a shell command. It does not
run training, read a dataset deeply, or write model outputs.
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


def q(value) -> str:
    return shlex.quote(str(value))


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit a gaussian-splatting train.py command")
    parser.add_argument("--repo-root", default=".", help="Checkout or install root containing train.py; used only in emitted command.")
    parser.add_argument("--source", required=True, help="Scene path for -s/--source_path.")
    parser.add_argument("--model", help="Output model path for -m/--model_path.")
    parser.add_argument("--images", default="images", help="COLMAP image subdirectory; default images.")
    parser.add_argument("--depths", help="Depth-map folder relative to source, for -d/--depths.")
    parser.add_argument("--iterations", type=int, default=30000)
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--resolution", type=int, help="1,2,4,8 for downscale factors, -1 default, or target width.")
    parser.add_argument("--white-background", action="store_true")
    parser.add_argument("--data-device", choices=["cuda", "cpu"], default="cuda")
    parser.add_argument("--disable-viewer", action="store_true")
    parser.add_argument("--ip", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=6009)
    parser.add_argument("--test-iterations", nargs="*", type=int)
    parser.add_argument("--save-iterations", nargs="*", type=int)
    parser.add_argument("--checkpoint-iterations", nargs="*", type=int)
    parser.add_argument("--start-checkpoint")
    parser.add_argument("--antialiasing", action="store_true")
    parser.add_argument("--train-test-exp", action="store_true")
    parser.add_argument("--exposure-preset", action="store_true", help="Add README exposure-compensation learning-rate flags.")
    parser.add_argument("--optimizer-type", choices=["default", "sparse_adam"], default="default")
    parser.add_argument("--low-vram-preset", action="store_true", help="Add conservative flags that reduce memory spikes; quality may change.")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if args.iterations <= 0:
        parser.error("--iterations must be positive")
    if args.optimizer_type == "sparse_adam":
        print("# WARNING: --optimizer_type sparse_adam requires the accelerated rasterizer variant exposing SparseGaussianAdam.")
    if args.depths:
        print("# NOTE: real COLMAP depth regularization also needs sparse/0/depth_params.json.")
    if args.low_vram_preset:
        print("# NOTE: low-vram preset changes training behavior and may reduce quality.")

    train_py = Path(args.repo_root) / "train.py"
    cmd = ["python", str(train_py), "-s", args.source, "--iterations", str(args.iterations)]
    if args.model:
        cmd += ["-m", args.model]
    if args.images != "images":
        cmd += ["-i", args.images]
    if args.depths:
        cmd += ["-d", args.depths]
    if args.eval:
        cmd.append("--eval")
    if args.resolution is not None:
        cmd += ["-r", str(args.resolution)]
    if args.white_background:
        cmd.append("--white_background")
    if args.data_device != "cuda":
        cmd += ["--data_device", args.data_device]
    if args.disable_viewer:
        cmd.append("--disable_viewer")
    else:
        cmd += ["--ip", args.ip, "--port", str(args.port)]
    if args.test_iterations is not None:
        cmd += ["--test_iterations", *map(str, args.test_iterations or [-1])]
    if args.save_iterations is not None:
        cmd += ["--save_iterations", *map(str, args.save_iterations or [args.iterations])]
    if args.checkpoint_iterations:
        cmd += ["--checkpoint_iterations", *map(str, args.checkpoint_iterations)]
    if args.start_checkpoint:
        cmd += ["--start_checkpoint", args.start_checkpoint]
    if args.antialiasing:
        cmd.append("--antialiasing")
    if args.train_test_exp:
        cmd.append("--train_test_exp")
    if args.exposure_preset:
        cmd += [
            "--exposure_lr_init", "0.001",
            "--exposure_lr_final", "0.0001",
            "--exposure_lr_delay_steps", "5000",
            "--exposure_lr_delay_mult", "0.001",
            "--train_test_exp",
        ]
    if args.optimizer_type != "default":
        cmd += ["--optimizer_type", args.optimizer_type]
    if args.low_vram_preset:
        cmd += ["--test_iterations", "-1", "--densify_grad_threshold", "0.0005", "--densification_interval", "200", "--densify_until_iter", str(min(args.iterations, 7000))]
    if args.quiet:
        cmd.append("--quiet")

    print(" ".join(q(part) for part in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
