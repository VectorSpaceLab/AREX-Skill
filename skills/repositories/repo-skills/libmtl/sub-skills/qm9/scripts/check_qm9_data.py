#!/usr/bin/env python3
"""Validate the bundled QM9 split artifact and optional dataset root."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch


def main() -> None:
    parser = argparse.ArgumentParser(description="Check the QM9 split artifact")
    parser.add_argument("--dataset-root", type=Path, default=None, help="optional QM9 dataset root")
    parser.add_argument(
        "--split",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "references" / "random_split.t",
        help="path to the bundled split artifact",
    )
    args = parser.parse_args()

    split_path = args.split.expanduser().resolve()
    if not split_path.is_file():
        raise SystemExit(f"missing split artifact: {split_path}")

    split = torch.load(split_path)
    print(f"split type: {type(split).__name__}")
    try:
        print(f"split length: {len(split)}")
    except Exception:
        pass

    if args.dataset_root is not None:
        root = args.dataset_root.expanduser().resolve()
        if not root.is_dir():
            raise SystemExit(f"missing dataset root: {root}")
        print(f"dataset root: {root}")

    print("qm9 data layout: ok")


if __name__ == "__main__":
    main()
