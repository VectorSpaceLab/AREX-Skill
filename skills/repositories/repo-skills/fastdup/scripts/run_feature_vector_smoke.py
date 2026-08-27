#!/usr/bin/env python3
"""Exercise binary feature save/load helpers with a tiny synthetic matrix."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import fastdup


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny binary-feature smoke test")
    parser.add_argument("--root", required=True, help="Workspace root for feature files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)

    filenames = [str(root / f"img-{i}.png") for i in range(3)]
    vec = np.arange(12, dtype="float32").reshape(3, 4)
    feat_dir = root / "features"

    rc = fastdup.save_binary_feature(str(feat_dir), filenames, vec)
    if rc != 0:
        raise RuntimeError(f"save_binary_feature returned {rc}")

    loaded_files, loaded_mat = fastdup.load_binary_feature(str(feat_dir), d=4)
    print(f"saved={len(filenames)} loaded={len(loaded_files)} shape={loaded_mat.shape}")
    print(f"first_filename={loaded_files[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
