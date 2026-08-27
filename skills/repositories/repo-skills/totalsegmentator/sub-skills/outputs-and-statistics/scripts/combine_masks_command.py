#!/usr/bin/env python3
"""Build a totalseg_combine_masks command without executing it."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path


MODE_CLASSES = {
    "lung": [
        "lung_upper_lobe_left",
        "lung_lower_lobe_left",
        "lung_upper_lobe_right",
        "lung_middle_lobe_right",
        "lung_lower_lobe_right",
    ],
    "lung_left": ["lung_upper_lobe_left", "lung_lower_lobe_left"],
    "lung_right": ["lung_upper_lobe_right", "lung_middle_lobe_right", "lung_lower_lobe_right"],
    "ribs": [*(f"rib_left_{idx}" for idx in range(1, 13)), *(f"rib_right_{idx}" for idx in range(1, 13))],
    "pelvis": ["femur_left", "femur_right", "hip_left", "hip_right"],
    "body": ["body_trunc", "body_extremities"],
}

CLI_MODES = ["lung", "lung_left", "lung_right", "vertebrae", "ribs", "vertebrae_ribs", "heart", "pelvis", "body"]


def _quote_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def _existing_missing(input_path: Path, mode: str) -> list[str] | None:
    classes = MODE_CLASSES.get(mode)
    if classes is None or not input_path.is_dir():
        return None
    return [class_name for class_name in classes if not (input_path / f"{class_name}.nii.gz").exists()]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build, but do not run, a totalseg_combine_masks command."
    )
    parser.add_argument("--input", "-i", required=True, type=Path, help="Per-class output directory or multilabel NIfTI input.")
    parser.add_argument("--output", "-o", required=True, type=Path, help="Output NIfTI path for the combined mask.")
    parser.add_argument("--mode", "-m", required=True, choices=CLI_MODES, help="Combination mode accepted by totalseg_combine_masks.")
    parser.add_argument("--multilabel", "-ml", action="store_true", help="Add --multilabel to create a labeled output image.")
    parser.add_argument("--nora-tag", default=None, help="Optional nora tag passed through as --nora_tag.")
    parser.add_argument("--check-input", action="store_true", help="For known directory modes, report missing source masks.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of only the shell command.")
    args = parser.parse_args()

    command = [
        "totalseg_combine_masks",
        "-i",
        str(args.input),
        "-o",
        str(args.output),
        "-m",
        args.mode,
    ]
    if args.multilabel:
        command.append("--multilabel")
    if args.nora_tag is not None:
        command.extend(["--nora_tag", args.nora_tag])

    missing = _existing_missing(args.input, args.mode) if args.check_input else None
    warnings: list[str] = []
    if args.mode == "heart":
        warnings.append("The CLI accepts heart mode, but verify behavior in the installed version before relying on it.")
    if missing:
        warnings.append("Missing source masks for this mode: " + ", ".join(missing))
    if args.input.is_file() and args.input.suffixes[-2:] == [".nii", ".gz"]:
        warnings.append("Multilabel input requires a readable label-map extension for class-name lookup.")

    shell_command = _quote_command(command)

    if args.json:
        print(json.dumps({"command": command, "shell_command": shell_command, "warnings": warnings}, indent=2))
    else:
        print(shell_command)
        for warning in warnings:
            print(f"WARNING: {warning}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
