#!/usr/bin/env python3
"""Validate a NanoDet config and optionally build its model.

Usage:
    python check_config.py --config path/to/config.yml
"""

from __future__ import annotations

import argparse
from pathlib import Path

from nanodet.model.arch import build_model
from nanodet.util import cfg, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a NanoDet config and build its model.",
    )
    parser.add_argument("--config", required=True, help="Path to a NanoDet YAML config.")
    parser.add_argument(
        "--no-build-model",
        action="store_true",
        help="Only load and validate the config without constructing the model.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    load_config(cfg, str(config_path))

    if cfg.model.arch.head.num_classes != len(cfg.class_names):
        raise ValueError(
            "cfg.model.arch.head.num_classes must equal len(cfg.class_names), "
            f"but got {cfg.model.arch.head.num_classes} and {len(cfg.class_names)}"
        )

    print(f"config: {config_path}")
    print(f"save_dir: {cfg.save_dir}")
    print(f"model: {cfg.model.arch.name}")
    print(f"backbone: {cfg.model.arch.backbone.name}")
    if "fpn" in cfg.model.arch:
        print(f"fpn: {cfg.model.arch.fpn.name}")
    print(f"head: {cfg.model.arch.head.name}")
    print(f"classes: {len(cfg.class_names)}")
    print(f"train dataset: {cfg.data.train.name}")
    print(f"val dataset: {cfg.data.val.name}")

    if not args.no_build_model:
        model = build_model(cfg.model)
        print(f"built_model: {type(model).__name__}")
        print(f"built_backbone: {type(model.backbone).__name__}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
