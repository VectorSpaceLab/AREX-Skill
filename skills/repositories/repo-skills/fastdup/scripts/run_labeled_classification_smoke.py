#!/usr/bin/env python3
"""Run a small labeled-image workflow on synthetic data."""

from __future__ import annotations

import argparse
from pathlib import Path

import fastdup
from fastdup.synthetic_image_data import create_synthetic_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny labeled-classification smoke test")
    parser.add_argument("--root", required=True, help="Workspace root for images and work_dir")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root)
    img_dir = root / "images"
    work_dir = root / "work"
    img_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    annot, *_ = create_synthetic_data(str(img_dir), n_valid=5, n_corrupted=1, n_duplicated=1, n_no_annotation=1, n_no_image=1)
    annot = annot.copy()
    annot["filename"] = annot["filename"].apply(lambda name: str(img_dir / name))

    fd = fastdup.create(work_dir=str(work_dir), input_dir=str(img_dir))
    ret = fd.run(annotations=annot, num_images=20, print_summary=False, verbose=False)
    if ret != 0:
        raise RuntimeError(f"fastdup run returned {ret}")

    print(f"similarity_rows={len(fd.similarity())}")
    print(f"component_gallery={fd.vis.component_gallery(num_images=3, show=False)}")
    print(f"outliers_gallery={fd.vis.outliers_gallery(num_images=3, show=False)}")
    print(f"stats_gallery={fd.vis.stats_gallery(num_images=3, show=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
