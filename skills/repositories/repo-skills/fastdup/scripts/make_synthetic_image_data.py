#!/usr/bin/env python3
"""Create a tiny synthetic image dataset for fastdup smoke tests.

Usage:
  python make_synthetic_image_data.py --output-dir /tmp/fastdup-fixture
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from fastdup.synthetic_image_data import create_synthetic_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a synthetic image dataset for fastdup")
    parser.add_argument("--output-dir", required=True, help="Directory that will receive PNG fixtures")
    parser.add_argument("--valid", type=int, default=4, help="Number of valid images")
    parser.add_argument("--corrupted", type=int, default=1, help="Number of corrupted images")
    parser.add_argument("--duplicated", type=int, default=1, help="Number of duplicated image pairs")
    parser.add_argument("--no-annotation", type=int, default=1, help="Number of images missing from the annotation dataframe")
    parser.add_argument("--no-image", type=int, default=1, help="Number of annotation rows without a matching file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    annot, valid, corrupted, not_in_annot, duplicated, no_image = create_synthetic_data(
        str(output_dir),
        n_valid=args.valid,
        n_corrupted=args.corrupted,
        n_duplicated=args.duplicated,
        n_no_annotation=args.no_annotation,
        n_no_image=args.no_image,
    )

    annot.to_csv(output_dir / "annotations.csv", index=False)
    valid.to_csv(output_dir / "valid.csv", index=False)
    corrupted.to_csv(output_dir / "corrupted.csv", index=False)
    not_in_annot.to_csv(output_dir / "not_in_annot.csv", index=False)
    duplicated.to_csv(output_dir / "duplicated.csv", index=False)
    no_image.to_csv(output_dir / "no_image.csv", index=False)

    print(f"wrote synthetic images to {output_dir}")
    print(f"annotation rows: {len(annot)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
