#!/usr/bin/env python3
"""Read-only schema validator for BigGAN-PyTorch ImageNet HDF5 files.

This intentionally checks metadata without materializing the image dataset.
Use --check-label-range when a full label scan is acceptable.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the metadata/schema expected by ILSVRC_HDF5."
    )
    parser.add_argument("path", type=Path, help="HDF5 file to inspect")
    parser.add_argument("--resolution", type=int, help="Expected square resolution")
    parser.add_argument("--classes", type=int, help="Expected number of classes")
    parser.add_argument(
        "--check-label-range",
        action="store_true",
        help="Scan labels and require 0 <= label < --classes (or 1000)",
    )
    return parser.parse_args()


def validate(args: argparse.Namespace) -> int:
    try:
        import h5py
    except ImportError:
        print("ERROR: h5py is required to inspect an HDF5 file.", file=sys.stderr)
        return 2

    errors = []
    if not args.path.is_file():
        print(f"ERROR: file does not exist: {args.path}", file=sys.stderr)
        return 2

    try:
        with h5py.File(args.path, "r") as handle:
            required = {"imgs", "labels"}
            missing = sorted(required.difference(handle.keys()))
            if missing:
                errors.append(f"missing datasets: {', '.join(missing)}")
            if errors:
                return report(args.path, errors)

            imgs = handle["imgs"]
            labels = handle["labels"]
            print(f"file: {args.path}")
            print(f"imgs: shape={imgs.shape}, dtype={imgs.dtype}, chunks={imgs.chunks}, compression={imgs.compression}")
            print(f"labels: shape={labels.shape}, dtype={labels.dtype}, chunks={labels.chunks}, compression={labels.compression}")

            if imgs.ndim != 4 or imgs.shape[1] != 3:
                errors.append("imgs must have shape (N, 3, size, size)")
            elif imgs.shape[2] != imgs.shape[3]:
                errors.append("imgs must be square in its last two dimensions")
            if labels.ndim != 1:
                errors.append("labels must have shape (N,)")
            if imgs.ndim >= 1 and labels.ndim >= 1 and imgs.shape[0] != labels.shape[0]:
                errors.append("imgs and labels must have the same N")
            if imgs.ndim >= 1 and imgs.shape[0] == 0:
                errors.append("imgs must contain at least one sample")
            if imgs.dtype.name != "uint8":
                errors.append(f"imgs dtype must be uint8, got {imgs.dtype}")
            if labels.dtype.name != "int64":
                errors.append(f"labels dtype must be int64, got {labels.dtype}")

            if args.resolution is not None and imgs.ndim == 4:
                if imgs.shape[2:] != (args.resolution, args.resolution):
                    errors.append(
                        f"expected resolution {args.resolution}, got {imgs.shape[2:]}"
                    )

            class_count = args.classes if args.classes is not None else 1000
            if args.check_label_range and labels.ndim == 1:
                # Read labels in bounded slices; image payload is never read.
                block = max(1, min(int(labels.shape[0]), 1_000_000))
                low = None
                high = None
                for start in range(0, int(labels.shape[0]), block):
                    values = labels[start : start + block]
                    if len(values):
                        part_low = int(values.min())
                        part_high = int(values.max())
                        low = part_low if low is None else min(low, part_low)
                        high = part_high if high is None else max(high, part_high)
                if low is not None:
                    print(f"label range: [{low}, {high}]")
                    if low < 0 or high >= class_count:
                        errors.append(
                            f"labels must lie in [0, {class_count - 1}], got [{low}, {high}]"
                        )
    except (OSError, ValueError, TypeError) as exc:
        print(f"ERROR: could not inspect {args.path}: {exc}", file=sys.stderr)
        return 2

    return report(args.path, errors)


def report(path: Path, errors: list[str]) -> int:
    if errors:
        print(f"INVALID: {path}", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("VALID: metadata matches the ILSVRC_HDF5 contract")
    return 0


def main() -> int:
    return validate(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
