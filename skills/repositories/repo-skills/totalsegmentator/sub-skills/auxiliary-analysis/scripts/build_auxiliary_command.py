#!/usr/bin/env python3
"""Build safe TotalSegmentator auxiliary-analysis commands.

This helper prints shell-quoted CLI commands for secondary TotalSegmentator
analysis tools. It never imports TotalSegmentator, opens image files, downloads
weights, or runs model inference.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import Iterable

VALID_DEVICES_NOTE = "cpu, gpu, gpu:N, or mps"


def quote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts if part is not None and str(part) != "")


def add_common_io(parser: argparse.ArgumentParser, *, output_required: bool = True) -> None:
    parser.add_argument("-i", "--input", required=True, help="Input image path.")
    parser.add_argument("-o", "--output", required=output_required, help="Output JSON path.")


def add_device(parser: argparse.ArgumentParser, default: str) -> None:
    parser.add_argument("-d", "--device", default=default, help=f"Execution device ({VALID_DEVICES_NOTE}).")


def add_quiet(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-q", "--quiet", action="store_true", help="Add the CLI quiet flag.")


def add_subprocess(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--call-via-subprocess",
        action="store_true",
        help="Ask the TotalSegmentator helper to call internal models via subprocess.",
    )


def validate_parent(path_value: str | None, warnings: list[str], label: str) -> None:
    if not path_value:
        return
    parent = Path(path_value).expanduser().parent
    if str(parent) not in ("", ".") and not parent.exists():
        warnings.append(f"{label} parent directory does not exist yet: {parent}")


def build_phase(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    command = ["totalseg_get_phase", "-i", args.input, "-o", args.output]
    warnings = [
        "Requires xgboost and packaged contrast-phase classifier resources.",
        "May run internal TotalSegmentator segmentation unless --existing-stats is supplied.",
    ]
    if args.model:
        command += ["-m", args.model]
    if args.existing_stats:
        command += ["-s", args.existing_stats]
        warnings.append("Existing statistics must contain compatible median-intensity ROI keys.")
    command += ["-d", args.device]
    if args.quiet:
        command.append("-q")
    if args.call_via_subprocess:
        command.append("--call_via_subprocess")
    if args.debug:
        command.append("--debug")
    validate_parent(args.output, warnings, "Output JSON")
    return command, warnings


def build_modality(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    command = ["totalseg_get_modality", "-i", args.input, "-o", args.output]
    warnings = ["Requires xgboost and packaged modality classifier resources."]
    if args.normalized_intensities:
        command.append("-n")
        command += ["-d", args.device]
        warnings.append("Normalized-intensity mode runs internal TotalSegmentator segmentation and is slower.")
    elif args.device != "gpu":
        warnings.append("Device is ignored unless --normalized-intensities is used.")
    if args.quiet:
        command.append("-q")
    validate_parent(args.output, warnings, "Output JSON")
    return command, warnings


def build_body_stats(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    command = [
        "totalseg_get_body_stats",
        "-i",
        args.input,
        "-m",
        args.modality,
        "--model_type",
        args.model_type,
        "-d",
        args.device,
    ]
    warnings = ["Body-stats commands can download/load model weights and run internal segmentation."]
    if args.output:
        command += ["-o", args.output]
        validate_parent(args.output, warnings, "Output JSON")
    else:
        warnings.append("No output JSON path was requested; result will print to stdout only.")
    if args.model_file:
        command += ["-mf", args.model_file]
    if args.only_weight:
        command.append("--only_weight")
    if args.fold is not None:
        if args.fold < 0 or args.fold > 4:
            raise SystemExit("--fold must be between 0 and 4")
        command += ["-f", str(args.fold)]
    if args.license_number:
        command += ["-l", args.license_number]
    if args.quiet:
        command.append("-q")
    if args.call_via_subprocess:
        command.append("--call_via_subprocess")
    if args.debug:
        command.append("--debug")
    if args.model_type == "cnn":
        warnings.append("CNN body stats require torch, timm, and sometimes monai checkpoint metadata support.")
    else:
        warnings.append("XGBoost body stats require xgboost and licensed tissue_types/tissue_types_mr segmentation.")
        if not args.license_number:
            warnings.append("No license was added; XGBoost body stats may fail on tissue-type tasks.")
    return command, warnings


def build_evans_index(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    command = ["totalseg_evans_index", "-i", args.input, "-o", args.output, "-p", args.preview]
    warnings = [
        "Requires antspyx importable as ants and blosc before calculation starts.",
        "Runs internal brain/skull and ventricle segmentation plus registration; inspect the preview PNG.",
    ]
    if args.verbose:
        command.append("-v")
    validate_parent(args.output, warnings, "Output JSON")
    validate_parent(args.preview, warnings, "Preview PNG")
    return command, warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print shell-quoted TotalSegmentator auxiliary-analysis commands without running models.",
    )
    subparsers = parser.add_subparsers(dest="tool", required=True)

    phase = subparsers.add_parser("phase", help="Build a totalseg_get_phase command.")
    add_common_io(phase)
    phase.add_argument("--model", help="Optional classifier model pickle path.")
    phase.add_argument("--existing-stats", help="Existing statistics JSON to avoid the initial segmentation run.")
    add_device(phase, "gpu")
    add_quiet(phase)
    add_subprocess(phase)
    phase.add_argument("--debug", action="store_true", help="Add --debug to the generated command.")
    phase.set_defaults(builder=build_phase)

    modality = subparsers.add_parser("modality", help="Build a totalseg_get_modality command.")
    add_common_io(modality)
    modality.add_argument(
        "--normalized-intensities",
        action="store_true",
        help="Use ROI-based normalized-intensity mode (-n).",
    )
    add_device(modality, "gpu")
    add_quiet(modality)
    modality.set_defaults(builder=build_modality)

    body_stats = subparsers.add_parser("body-stats", help="Build a totalseg_get_body_stats command.")
    add_common_io(body_stats, output_required=False)
    body_stats.add_argument("-m", "--modality", choices=["ct", "mr"], required=True, help="Input modality.")
    body_stats.add_argument("--model-type", choices=["cnn", "xgboost"], default="cnn", help="Prediction backend.")
    body_stats.add_argument("--model-file", help="Classifier base path or CNN experiment directory.")
    body_stats.add_argument("--only-weight", action="store_true", help="Predict only body weight.")
    body_stats.add_argument("--fold", type=int, help="Single fold to use (0-4); omit for ensemble.")
    body_stats.add_argument("--license-number", help="License number for licensed tissue-type tasks.")
    add_device(body_stats, "cpu")
    add_quiet(body_stats)
    add_subprocess(body_stats)
    body_stats.add_argument("--debug", action="store_true", help="Add --debug to the generated command.")
    body_stats.set_defaults(builder=build_body_stats)

    evans = subparsers.add_parser("evans-index", help="Build a totalseg_evans_index command.")
    add_common_io(evans)
    evans.add_argument("-p", "--preview", required=True, help="Preview PNG output path.")
    evans.add_argument("-v", "--verbose", action="store_true", help="Add verbose progress flag.")
    evans.set_defaults(builder=build_evans_index)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    command, warnings = args.builder(args)
    print(quote_command(command))
    if warnings:
        print("\nWarnings:", file=sys.stderr)
        for warning in warnings:
            print(f"- {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
