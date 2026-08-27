#!/usr/bin/env python3
"""Safely inspect the segmentation-training CLI contract.

This helper intentionally has no project imports. In particular, it does not
import segmentation_train.py, Visdom, torch, datasets, or model code.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


# These two dictionaries mirror the literal defaults in segmentation_train.py
# and guided_diffusion.script_util.py. Keep option names exact.
TRAIN_DEFAULTS = {
    "data_name": "BRATS",
    "data_dir": "../dataset/brats2020/training",
    "schedule_sampler": "uniform",
    "lr": 1e-4,
    "weight_decay": 0.0,
    "lr_anneal_steps": 0,
    "batch_size": 1,
    "microbatch": -1,
    "ema_rate": "0.9999",
    "log_interval": 100,
    "save_interval": 5000,
    "resume_checkpoint": None,
    "use_fp16": False,
    "fp16_scale_growth": 1e-3,
    "gpu_dev": "0",
    "multi_gpu": None,
    "out_dir": "./results/",
}

MODEL_DIFFUSION_DEFAULTS = {
    "image_size": 64,
    "num_channels": 128,
    "num_res_blocks": 2,
    "num_heads": 4,
    "in_ch": 5,
    "num_heads_upsample": -1,
    "num_head_channels": -1,
    "attention_resolutions": "16,8",
    "channel_mult": "",
    "dropout": 0.0,
    "class_cond": False,
    "use_checkpoint": False,
    "use_scale_shift_norm": True,
    "resblock_updown": False,
    "use_fp16": False,
    "use_new_attention_order": False,
    "dpm_solver": False,
    "version": "new",
    "learn_sigma": False,
    "diffusion_steps": 1000,
    "noise_schedule": "linear",
    "timestep_respacing": "",
    "use_kl": False,
    "predict_xstart": False,
    "rescale_timesteps": False,
    "rescale_learned_sigmas": False,
}

DEFAULTS = dict(TRAIN_DEFAULTS)
DEFAULTS.update(MODEL_DIFFUSION_DEFAULTS)


def str2bool(value: Any) -> bool:
    """Match the source parser's explicit boolean conversion."""
    if isinstance(value, bool):
        return value
    token = value.lower()
    if token in ("yes", "true", "t", "y", "1"):
        return True
    if token in ("no", "false", "f", "n", "0"):
        return False
    raise argparse.ArgumentTypeError("boolean value expected")


def _type_for(default: Any):
    if default is None:
        return str
    if isinstance(default, bool):
        return str2bool
    return type(default)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="inspect_train_cli.py",
        description=(
            "Safe inspection of the MedSegDiff segmentation_train.py CLI; "
            "does not import or start training."
        ),
    )
    for name, default in DEFAULTS.items():
        parser.add_argument(f"--{name}", default=default, type=_type_for(default))
    parser.add_argument(
        "--show-defaults",
        action="store_true",
        help="print the embedded effective parser defaults as JSON",
    )
    parser.add_argument(
        "--show-branch",
        action="store_true",
        help="report the source branch selected by data_name and data_dir",
    )
    return parser


def source_branch(data_name: str, data_dir: str) -> dict[str, Any]:
    """Mirror branch precedence without opening files or importing loaders."""
    if data_name == "ISIC":
        return {"branch": "ISIC", "assigned_in_ch": 4, "reason": "exact data_name"}
    if data_name == "BRATS":
        return {"branch": "BRATS", "assigned_in_ch": 5, "reason": "exact data_name"}

    pattern = r"*\*.nii.gz"
    try:
        has_nii = any(Path(data_dir).glob(pattern))
    except (OSError, ValueError, NotImplementedError) as exc:
        return {
            "branch": "custom-2d-fallback",
            "assigned_in_ch": 4,
            "reason": "glob inspection failed; source falls through",
            "glob_pattern": pattern,
            "glob_error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "branch": "custom-3d",
        "assigned_in_ch": 4,
        "reason": "source glob matched",
        "glob_pattern": pattern,
    } if has_nii else {
        "branch": "custom-2d-fallback",
        "assigned_in_ch": 4,
        "reason": "source glob did not match",
        "glob_pattern": pattern,
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not (args.show_defaults or args.show_branch):
        parser.print_help()
        return 0

    if args.show_defaults:
        print(json.dumps(DEFAULTS, indent=2, sort_keys=True))
    if args.show_branch:
        report = source_branch(args.data_name, args.data_dir)
        report["data_name"] = args.data_name
        report["data_dir"] = args.data_dir
        report["note"] = (
            "This mirrors the literal source glob. On POSIX, the backslash in "
            "*\\*.nii.gz may not match ordinary nested .nii.gz files."
        )
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
