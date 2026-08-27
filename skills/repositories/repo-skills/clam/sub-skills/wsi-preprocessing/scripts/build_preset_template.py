#!/usr/bin/env python3
"""Create a portable CLAM segmentation preset CSV without writing into a repo presets directory."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

FIELDNAMES = [
    "seg_level",
    "sthresh",
    "mthresh",
    "close",
    "use_otsu",
    "a_t",
    "a_h",
    "max_n_holes",
    "vis_level",
    "line_thickness",
    "white_thresh",
    "black_thresh",
    "use_padding",
    "contour_fn",
    "keep_ids",
    "exclude_ids",
]


def odd_positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0 or parsed % 2 == 0:
        raise argparse.ArgumentTypeError("must be a positive odd integer")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def build_row(args: argparse.Namespace) -> dict[str, object]:
    return {
        "seg_level": args.seg_level,
        "sthresh": args.sthresh,
        "mthresh": args.mthresh,
        "close": args.close,
        "use_otsu": bool_text(args.use_otsu),
        "a_t": args.a_t,
        "a_h": args.a_h,
        "max_n_holes": args.max_n_holes,
        "vis_level": args.vis_level,
        "line_thickness": args.line_thickness,
        "white_thresh": args.white_thresh,
        "black_thresh": args.black_thresh,
        "use_padding": bool_text(not args.no_padding),
        "contour_fn": args.contour_fn,
        "keep_ids": args.keep_ids,
        "exclude_ids": args.exclude_ids,
    }


def write_csv(destination, row: dict[str, object]) -> None:
    writer = csv.DictWriter(destination, fieldnames=FIELDNAMES, lineterminator="\n")
    writer.writeheader()
    writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print or write a CLAM preset CSV with the expected parameter columns."
    )
    parser.add_argument("--preset_name", help="logical preset filename to record in messages")
    parser.add_argument("--output", help="write CSV to this path; omit to print to stdout")
    parser.add_argument("--seg_level", type=int, default=-1, help="segmentation level, -1 chooses ~64x downsample")
    parser.add_argument("--sthresh", type=nonnegative_int, default=8, help="HSV saturation threshold")
    parser.add_argument("--mthresh", type=odd_positive_int, default=7, help="median filter size")
    parser.add_argument("--use_otsu", action="store_true", help="use Otsu thresholding")
    parser.add_argument("--close", type=int, default=4, help="morphological closing kernel; <=0 disables")
    parser.add_argument("--a_t", type=nonnegative_int, default=100, help="tissue area filter")
    parser.add_argument("--a_h", type=nonnegative_int, default=16, help="hole area filter")
    parser.add_argument("--max_n_holes", type=nonnegative_int, default=8, help="maximum holes per contour")
    parser.add_argument("--vis_level", type=int, default=-1, help="visualization level, -1 chooses ~64x downsample")
    parser.add_argument("--line_thickness", type=nonnegative_int, default=250, help="mask contour line thickness")
    parser.add_argument("--white_thresh", type=nonnegative_int, default=5, help="legacy saved-patch blank filter")
    parser.add_argument("--black_thresh", type=nonnegative_int, default=50, help="legacy saved-patch black filter")
    parser.add_argument("--no_padding", action="store_true", help="set use_padding to FALSE")
    parser.add_argument(
        "--contour_fn",
        choices=["four_pt", "center", "basic", "four_pt_hard"],
        default="four_pt",
        help="foreground contour check function",
    )
    parser.add_argument("--keep_ids", default="none", help="comma-separated contour ids to keep, or none")
    parser.add_argument("--exclude_ids", default="none", help="comma-separated contour ids to exclude, or none")
    args = parser.parse_args()

    if args.output:
        output_path = Path(args.output)
        if output_path.exists() and output_path.is_dir():
            parser.error("--output must be a file path, not a directory")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="") as handle:
            write_csv(handle, build_row(args))
        preset_name = args.preset_name or output_path.name
        print(f"Wrote CLAM preset {preset_name!r} to {output_path}")
    else:
        write_csv(sys.stdout, build_row(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
