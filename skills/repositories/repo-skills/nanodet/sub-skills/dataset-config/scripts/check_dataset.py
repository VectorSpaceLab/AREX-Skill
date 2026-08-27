#!/usr/bin/env python3
"""Build a NanoDet dataset from a config and inspect one sample.

Usage:
    python check_dataset.py --config path/to/config.yml --split train
"""

from __future__ import annotations

import argparse
from pathlib import Path

from nanodet.data.dataset import build_dataset
from nanodet.util import cfg, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a NanoDet dataset from a config and inspect a sample.",
    )
    parser.add_argument("--config", required=True, help="Path to a NanoDet YAML config.")
    parser.add_argument(
        "--split",
        choices=("train", "val", "test"),
        default="train",
        help="Which dataset section to build.",
    )
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help="Which sample index to inspect after building the dataset.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    load_config(cfg, str(config_path))

    section = cfg.data.train if args.split == "train" else cfg.data.val
    dataset = build_dataset(section, args.split)
    sample = dataset[args.index]

    print(f"config: {config_path}")
    print(f"split: {args.split}")
    print(f"dataset: {type(dataset).__name__}")
    print(f"length: {len(dataset)}")
    print(f"sample_keys: {sorted(sample.keys())}")
    img = sample.get("img")
    if hasattr(img, "shape"):
        print(f"sample_img_shape: {tuple(img.shape)}")
    if "gt_bboxes" in sample:
        print(f"sample_gt_bboxes: {getattr(sample['gt_bboxes'], 'shape', None)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
