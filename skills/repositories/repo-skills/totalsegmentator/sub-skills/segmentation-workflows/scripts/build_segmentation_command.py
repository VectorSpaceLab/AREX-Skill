#!/usr/bin/env python3
"""Build a shell-quoted TotalSegmentator segmentation command without running it."""

from __future__ import annotations

import argparse
import re
import shlex
import sys
from typing import Iterable

VALID_OUTPUT_TYPES = {"nifti", "dicom_seg", "dicom_rtstruct"}
DEVICE_PATTERN = re.compile(r"^(cpu|gpu|mps|gpu:\d+)$")


def valid_device(value: str) -> str:
    if DEVICE_PATTERN.match(value):
        return value
    raise argparse.ArgumentTypeError(
        "invalid device; use 'cpu', 'gpu', 'gpu:N' with a non-negative integer, or 'mps'"
    )


def resampling_order(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("resampling order must be an integer from 0 through 5") from exc
    if parsed < 0 or parsed > 5:
        raise argparse.ArgumentTypeError("resampling order must be from 0 through 5")
    return parsed


def normalize_output_types(values: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        for part in value.split(","):
            cleaned = part.strip()
            if cleaned == "dicom":
                cleaned = "dicom_rtstruct"
            if not cleaned:
                continue
            if cleaned not in VALID_OUTPUT_TYPES:
                allowed = ", ".join(sorted(VALID_OUTPUT_TYPES))
                raise argparse.ArgumentTypeError(f"invalid output type '{cleaned}'; allowed: {allowed}")
            normalized.append(cleaned)
    return normalized or ["nifti"]


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a validated, shell-quoted TotalSegmentator command. "
            "This helper never imports TotalSegmentator and never runs model inference."
        )
    )
    parser.add_argument("--input", "-i", required=True, help="Input NIfTI file, DICOM folder, or DICOM zip.")
    parser.add_argument("--output", "-o", required=True, help="Output directory, multilabel file, or DICOM output file.")
    parser.add_argument("--task", "-ta", default="total", help="TotalSegmentator task name, e.g. total or total_mr.")
    parser.add_argument("--device", "-d", default="gpu", type=valid_device, help="cpu, gpu, gpu:N, or mps.")
    parser.add_argument("--fast", action="store_true", help="Use the 3 mm lower-resolution model.")
    parser.add_argument("--fastest", action="store_true", help="Use the 6 mm lower-resolution model.")
    parser.add_argument(
        "--roi",
        "--roi-subset",
        dest="roi_subset",
        action="append",
        nargs="+",
        default=[],
        metavar="CLASS",
        help="Class name(s) for --roi_subset. May be repeated.",
    )
    parser.add_argument("--multilabel", "--ml", action="store_true", help="Save one multilabel NIfTI file.")
    parser.add_argument(
        "--statistics",
        nargs="?",
        const=True,
        default=False,
        metavar="PATH",
        help="Enable statistics; optionally provide a custom statistics JSON path.",
    )
    parser.add_argument("--statistics-extra", action="store_true", help="Add extra metrics to statistics output.")
    parser.add_argument("--report", help="Path for the machine-readable run report JSON.")
    parser.add_argument(
        "--output-type",
        action="append",
        default=[],
        metavar="TYPE",
        help="Output type: nifti, dicom_seg, dicom_rtstruct. Repeat or comma-separate for multiple.",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress intermediate TotalSegmentator output.")
    parser.add_argument("--debug", action="store_true", help="Request extra TotalSegmentator error context.")
    parser.add_argument("--save-lowres", action="store_true", help="Save fast/fastest output at model resolution.")
    parser.add_argument(
        "--resampling-order",
        type=resampling_order,
        default=3,
        help="Spline interpolation order for input resampling, 0 through 5. Default: 3.",
    )
    parser.add_argument(
        "--model-size",
        choices=["big", "small"],
        default="big",
        help="Model size. 'small' is only valid for task total_v3.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    output_types = normalize_output_types(args.output_type or ["nifti"])
    roi_subset = [roi for group in args.roi_subset for roi in group]

    if args.fast and args.fastest:
        parser.error("choose either --fast or --fastest, not both")
    if args.save_lowres and not (args.fast or args.fastest):
        parser.error("--save-lowres requires --fast or --fastest")
    if args.save_lowres and any(output_type != "nifti" for output_type in output_types):
        parser.error("--save-lowres only supports nifti output")
    if args.model_size == "small" and args.task != "total_v3":
        parser.error("--model-size small is only supported with --task total_v3")
    if args.statistics_extra and not args.statistics:
        print("WARNING: --statistics-extra is usually useful together with --statistics.", file=sys.stderr)
    if args.device == "cpu":
        print(
            "WARNING: CPU segmentation can be very slow; prefer --fast, --fastest, or --roi for constrained runs.",
            file=sys.stderr,
        )
    if args.save_lowres:
        print(
            "WARNING: --save_lowres preserves model-resolution output instead of upsampling to input resolution.",
            file=sys.stderr,
        )
    if args.multilabel and any(output_type != "nifti" for output_type in output_types):
        print("WARNING: --multilabel is intended for NIfTI output workflows.", file=sys.stderr)
    if not args.report:
        print("WARNING: add --report for reproducible automation and downstream parsing.", file=sys.stderr)

    command = [
        "TotalSegmentator",
        "-i",
        args.input,
        "-o",
        args.output,
        "-ta",
        args.task,
        "-d",
        args.device,
    ]

    if args.fast:
        command.append("--fast")
    if args.fastest:
        command.append("--fastest")
    if args.save_lowres:
        command.append("--save_lowres")
    if roi_subset:
        command.append("--roi_subset")
        command.extend(roi_subset)
    if args.multilabel:
        command.append("--ml")
    if args.statistics is not False:
        command.append("--statistics")
        if isinstance(args.statistics, str):
            command.append(args.statistics)
    if args.statistics_extra:
        command.append("--statistics_extra")
    if args.report:
        command.extend(["--report", args.report])
    if output_types != ["nifti"]:
        command.append("--output_type")
        command.extend(output_types)
    if args.resampling_order != 3:
        command.extend(["--resampling_order", str(args.resampling_order)])
    if args.model_size != "big":
        command.extend(["--model_size", args.model_size])
    if args.quiet:
        command.append("--quiet")
    if args.debug:
        command.append("--debug")

    print(shell_join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
