#!/usr/bin/env python3
"""Print safe single-GPU MambaVision MMDetection command templates.

This helper never launches training or evaluation. It validates known
MambaVision detection config ids and emits copyable command templates with
placeholder entry points and config roots by default. Replace those placeholders
with paths in the user's target checkout or project.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import PurePosixPath
from typing import Iterable


class HelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    pass


CONFIG_BASENAMES = {
    "tiny": "cascade_mask_rcnn_mamba_vision_tiny_3x_coco.py",
    "small": "cascade_mask_rcnn_mamba_vision_small_3x_coco.py",
    "base": "cascade_mask_rcnn_mamba_vision_base_3x_coco.py",
}

PLACEHOLDERS = {
    "config_root": "MAMBAVISION_DETECTION_CONFIG_ROOT",
    "train_entrypoint": "MMDET_TRAIN_ENTRYPOINT",
    "test_entrypoint": "MMDET_TEST_ENTRYPOINT",
    "data_root": "COCO_ROOT",
    "backbone_pretrained": "BACKBONE_PRETRAINED",
    "checkpoint": "DETECTOR_CHECKPOINT",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print safe single-GPU MMDetection command templates for MambaVision object detection.",
        formatter_class=HelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/print_mmdet_command.py --mode train --config-id tiny --config-root ./configs/mamba_vision --train-entrypoint TARGET_MMDET_TRAIN\n"
            "  python scripts/print_mmdet_command.py --mode test --config-id base --checkpoint ./work_dirs/base/epoch_36.pth --test-entrypoint TARGET_MMDET_TEST\n"
            "  python scripts/print_mmdet_command.py --mode both --config-id small --data-root /data/coco --config-root ./configs/mamba_vision\n"
        ),
    )
    parser.add_argument("--mode", choices=("train", "test", "both"), default="both", help="Which single-GPU command(s) to print.")
    parser.add_argument("--config-id", choices=tuple(CONFIG_BASENAMES), default="tiny", help="Known MambaVision detection family.")
    parser.add_argument("--config-root", default=PLACEHOLDERS["config_root"], help="Directory containing the selected MambaVision detection config in the target project.")
    parser.add_argument("--train-entrypoint", default=PLACEHOLDERS["train_entrypoint"], help="MMDetection training entry point in the target project.")
    parser.add_argument("--test-entrypoint", default=PLACEHOLDERS["test_entrypoint"], help="MMDetection test entry point in the target project.")
    parser.add_argument("--gpu", type=int, default=0, help="CUDA device index used in CUDA_VISIBLE_DEVICES.")
    parser.add_argument("--data-root", default=PLACEHOLDERS["data_root"], help="COCO root used in data_root overrides.")
    parser.add_argument("--backbone-pretrained", default=PLACEHOLDERS["backbone_pretrained"], help="Backbone checkpoint path for the train command.")
    parser.add_argument("--checkpoint", default=PLACEHOLDERS["checkpoint"], help="Detector checkpoint path for the test command.")
    parser.add_argument("--work-dir", default="", help="Optional explicit work directory appended to the command.")
    parser.add_argument("--cfg-option", action="append", default=[], metavar="KEY=VALUE", help="Extra cfg-options pairs appended to both commands.")
    return parser.parse_args()


def die(message: str, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def quote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def validate_cfg_options(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    for item in values:
        if "=" not in item:
            die(f"Invalid --cfg-option value {item!r}; expected KEY=VALUE.")
        cleaned.append(item)
    return cleaned


def config_path(args: argparse.Namespace) -> str:
    return str(PurePosixPath(args.config_root) / CONFIG_BASENAMES[args.config_id])


def build_train_command(args: argparse.Namespace, extra_cfg: list[str]) -> str:
    parts = ["env", f"CUDA_VISIBLE_DEVICES={args.gpu}", "python", args.train_entrypoint, config_path(args)]
    if args.work_dir:
        parts += ["--work-dir", args.work_dir]
    parts += ["--cfg-options", f"data_root={args.data_root}", f"model.backbone.pretrained={args.backbone_pretrained}"]
    parts.extend(extra_cfg)
    return quote_command(parts)


def build_test_command(args: argparse.Namespace, extra_cfg: list[str]) -> str:
    parts = ["env", f"CUDA_VISIBLE_DEVICES={args.gpu}", "python", args.test_entrypoint, config_path(args), args.checkpoint]
    if args.work_dir:
        parts += ["--work-dir", args.work_dir]
    parts += ["--eval", "bbox", "segm", "--cfg-options", f"data_root={args.data_root}"]
    parts.extend(extra_cfg)
    return quote_command(parts)


def main() -> int:
    args = parse_args()
    extra_cfg = validate_cfg_options(args.cfg_option)
    outputs: list[tuple[str, str]] = []
    if args.mode in ("train", "both"):
        outputs.append(("train", build_train_command(args, extra_cfg)))
    if args.mode in ("test", "both"):
        outputs.append(("test", build_test_command(args, extra_cfg)))
    for index, (label, command) in enumerate(outputs):
        if index:
            print()
        print(f"# {label}")
        print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
