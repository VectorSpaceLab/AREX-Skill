#!/usr/bin/env python3
"""Create a tiny synthetic bbox dataset for fastdup smoke tests.

Usage:
  python make_synthetic_bbox_data.py --output-dir /tmp/fastdup-bbox-fixture
"""

from __future__ import annotations

import argparse
from pathlib import Path

from fastdup.synthetic_bbox_data import create_synthetic_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a synthetic bbox dataset for fastdup")
    parser.add_argument("--output-dir", required=True, help="Directory that will receive PNG fixtures")
    parser.add_argument("--single", type=int, default=4, help="Number of single-bbox images")
    parser.add_argument("--double", type=int, default=3, help="Number of double-bbox images")
    parser.add_argument("--duplicated", type=int, default=1, help="Number of duplicated bbox pairs")
    parser.add_argument("--corrupted", type=int, default=1, help="Number of corrupted images")
    parser.add_argument("--no-image", type=int, default=1, help="Number of annotation rows without files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    annot, invalid_bbox, df_single, df_double, df_duplicate, df_corrupted, df_no_image = create_synthetic_data(
        str(output_dir),
        n_valid_single_bbox=args.single,
        n_valid_double_bbox=args.double,
        n_duplicated_bbox=args.duplicated,
        n_corrupted_image=args.corrupted,
        n_no_image=args.no_image,
    )

    annot.to_csv(output_dir / "annotations.csv", index=False)
    invalid_bbox.to_csv(output_dir / "invalid_bbox.csv", index=False)
    df_single.to_csv(output_dir / "single_bbox.csv", index=False)
    df_double.to_csv(output_dir / "double_bbox.csv", index=False)
    df_duplicate.to_csv(output_dir / "duplicated_bbox.csv", index=False)
    df_corrupted.to_csv(output_dir / "corrupted_bbox.csv", index=False)
    df_no_image.to_csv(output_dir / "no_image_bbox.csv", index=False)

    print(f"wrote synthetic bbox images to {output_dir}")
    print(f"annotation rows: {len(annot)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
