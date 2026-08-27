#!/usr/bin/env python3
"""Build a safe crop_to_body command for TotalSegmentator preprocessing.

The script prints a shell-quoted command only. It does not import TotalSegmentator,
load model weights, or run crop_to_body.
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


def nifti_path(value: str) -> str:
    if not (value.endswith(".nii") or value.endswith(".nii.gz")):
        raise argparse.ArgumentTypeError("crop_to_body expects a .nii or .nii.gz NIfTI path")
    return value


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def build_command(args: argparse.Namespace) -> list[str]:
    command = ["crop_to_body", "-i", args.input, "-o", args.output]
    if args.only_trunc:
        command.append("--only_trunc")
    if args.nr_thr_resamp != 1:
        command.extend(["--nr_thr_resamp", str(args.nr_thr_resamp)])
    if args.nr_thr_saving != 6:
        command.extend(["--nr_thr_saving", str(args.nr_thr_saving)])
    command.extend(["--device", args.device])
    if args.quiet:
        command.append("--quiet")
    if args.verbose:
        command.append("--verbose")
    return command


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print a shell-quoted crop_to_body command without executing it."
    )
    parser.add_argument("-i", "--input", required=True, type=nifti_path, help="Input CT NIfTI file (.nii or .nii.gz)")
    parser.add_argument("-o", "--output", required=True, type=nifti_path, help="Output cropped NIfTI file (.nii or .nii.gz)")
    parser.add_argument("-t", "--only-trunc", action="store_true", help="Crop to body trunk instead of entire body")
    parser.add_argument("-nr", "--nr-thr-resamp", type=positive_int, default=1, help="Threads for resampling")
    parser.add_argument("-ns", "--nr-thr-saving", type=positive_int, default=6, help="Threads for saving segmentations")
    parser.add_argument("-d", "--device", choices=["gpu", "cpu"], default="gpu", help="Device for crop_to_body")
    parser.add_argument("-q", "--quiet", action="store_true", help="Add --quiet")
    parser.add_argument("-v", "--verbose", action="store_true", help="Add --verbose")
    parser.add_argument("--absolute", action="store_true", help="Render input and output as absolute paths")
    args = parser.parse_args()

    if args.quiet and args.verbose:
        parser.error("choose either --quiet or --verbose, not both")

    if args.absolute:
        args.input = str(Path(args.input).absolute())
        args.output = str(Path(args.output).absolute())

    command = build_command(args)
    print(" ".join(shlex.quote(part) for part in command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
