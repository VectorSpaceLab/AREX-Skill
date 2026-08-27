#!/usr/bin/env python3
"""Run a small bbox workflow on synthetic detection data."""

from __future__ import annotations

import argparse
from pathlib import Path

import fastdup
from fastdup.synthetic_bbox_data import create_synthetic_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny labeled-detection smoke test")
    parser.add_argument("--root", required=True, help="Workspace root for images and work_dir")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root)
    img_dir = root / "images"
    work_dir = root / "work"
    img_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    annot, *_ = create_synthetic_data(str(img_dir), n_valid_single_bbox=4, n_valid_double_bbox=2, n_duplicated_bbox=1, n_corrupted_image=1, n_no_image=1)
    annot = annot.copy()
    annot["filename"] = annot["filename"].apply(lambda name: str(img_dir / name))

    fd = fastdup.create(work_dir=str(work_dir), input_dir=str(img_dir))
    ret = fd.run(annotations=annot, data_type="bbox", num_images=20, print_summary=False, verbose=False)
    if ret != 0:
        raise RuntimeError(f"fastdup run returned {ret}")

    print(f"similarity_rows={len(fd.similarity())}")
    # Some release lines have fragile draw_bbox=True gallery paths; the smoke
    # test verifies bbox analysis and gallery generation without relying on that optional rendering mode.
    print(f"component_gallery={fd.vis.component_gallery(num_images=3, show=False)}")
    print(f"outliers_gallery={fd.vis.outliers_gallery(num_images=3, show=False)}")
    print(f"stats_gallery={fd.vis.stats_gallery(num_images=3, show=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
