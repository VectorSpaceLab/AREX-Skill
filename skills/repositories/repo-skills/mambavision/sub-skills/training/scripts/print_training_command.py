#!/usr/bin/env python3
"""Print safe MambaVision ImageNet training command templates.

This helper never launches training. It validates known model/config ids and
emits a command template whose training entry point is a placeholder by default.
Replace the placeholder with the entry point in the user's target source
distribution or local project before running.
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import PurePosixPath

PRESETS = {
    "tiny": ("mambavision_tiny_1k.yaml", "mamba_vision_T", "3 224 224", "0.875", "0.2", "256", "0.005"),
    "tiny2": ("mambavision_tiny2_1k.yaml", "mamba_vision_T2", "3 224 224", "0.875", "0.2", "256", "0.005"),
    "small": ("mambavision_small_1k.yaml", "mamba_vision_S", "3 224 224", "0.875", "0.3", "192", "0.005"),
    "base": ("mambavision_base_1k.yaml", "mamba_vision_B", "3 224 224", "0.875", "0.3", "128", "0.005"),
    "large": ("mambavision_large_1k.yaml", "mamba_vision_L", "3 224 224", "0.875", "0.5", "64", "0.005"),
    "large2": ("mambavision_large2_1k.yaml", "mamba_vision_L2", "3 224 224", "0.875", "0.5", "64", "0.005"),
}


def quote(parts: list[str]) -> str:
    return " ".join(shlex.quote(p) for p in parts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a MambaVision ImageNet training command template.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--preset", choices=tuple(PRESETS), default="tiny", help="Known MambaVision 1K training preset.")
    parser.add_argument("--entrypoint", default="MAMBAVISION_TRAIN_ENTRYPOINT", help="Training script/module in the target project.")
    parser.add_argument("--config-root", default="MAMBAVISION_CONFIG_ROOT", help="Directory containing MambaVision YAML presets in the target project.")
    parser.add_argument("--data-dir", default="IMAGENET_ROOT", help="ImageNet/ImageFolder root.")
    parser.add_argument("--output", default="OUTPUT_ROOT", help="Experiment output root.")
    parser.add_argument("--tag", default="mambavision_run", help="Experiment tag.")
    parser.add_argument("--gpus", type=int, default=8, help="Number of GPUs/processes for torchrun. Use 1 for a single-process debug command.")
    parser.add_argument("--cuda-visible-devices", default="0,1,2,3,4,5,6,7", help="CUDA_VISIBLE_DEVICES value.")
    parser.add_argument("--train-split", default="train", help="Training split name.")
    parser.add_argument("--val-split", default="validation", help="Validation split name.")
    parser.add_argument("--batch-size", default=None, help="Override per-GPU batch size.")
    parser.add_argument("--lr", default=None, help="Override learning rate.")
    parser.add_argument("--drop-path", default=None, help="Override drop-path rate.")
    parser.add_argument("--weight-decay", default="0.05", help="Weight decay.")
    parser.add_argument("--debug-epochs", type=int, default=0, help="If >0, append --epochs and lower-worker debug flags.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_file, model, input_size, crop_pct, drop_path_default, batch_default, lr_default = PRESETS[args.preset]
    batch_size = args.batch_size or batch_default
    lr = args.lr or lr_default
    drop_path = args.drop_path or drop_path_default
    config_path = str(PurePosixPath(args.config_root) / config_file)

    launcher = ["python", args.entrypoint]
    if args.gpus > 1:
        launcher = ["torchrun", "--standalone", f"--nproc_per_node={args.gpus}", args.entrypoint]

    parts = ["env", f"CUDA_VISIBLE_DEVICES={args.cuda_visible_devices}", *launcher,
             "--config", config_path,
             "--data_dir", args.data_dir,
             "--train-split", args.train_split,
             "--val-split", args.val_split,
             "--output", args.output,
             "--tag", args.tag,
             "--model", model,
             "--input-size", *input_size.split(),
             "--crop-pct", crop_pct,
             "--batch-size", str(batch_size),
             "--lr", str(lr),
             "--weight-decay", str(args.weight_decay),
             "--drop-path", str(drop_path),
             "--amp", "--model-ema", "--channels-last"]
    if args.debug_epochs > 0:
        parts.extend(["--epochs", str(args.debug_epochs), "--workers", "2", "--no_saver"])
    print(quote(parts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
