#!/usr/bin/env python3
"""Build safe CLAM WSI preprocessing commands without touching WSI files."""

from __future__ import annotations

import argparse
import shlex
from pathlib import PurePath

PRESET_CHOICES = {"bwh_biopsy.csv", "bwh_resection.csv", "tcga.csv"}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def build_command(args: argparse.Namespace) -> list[str]:
    command = [
        "python",
        "create_patches_fp.py",
        "--source",
        args.source,
        "--save_dir",
        args.save_dir,
        "--patch_size",
        str(args.patch_size),
        "--step_size",
        str(args.step_size),
        "--patch_level",
        str(args.patch_level),
    ]
    if args.preset:
        command.extend(["--preset", args.preset])
    if args.process_list:
        command.extend(["--process_list", args.process_list])
    if args.seg:
        command.append("--seg")
    if args.patch:
        command.append("--patch")
    if args.stitch:
        command.append("--stitch")
    if args.no_auto_skip:
        command.append("--no_auto_skip")
    return command


def quote_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def output_layout(save_dir: str) -> list[str]:
    root = PurePath(save_dir)
    return [
        str(root / "masks"),
        str(root / "patches"),
        str(root / "stitches"),
        str(root / "process_list_autogen.csv"),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print a validated CLAM create_patches_fp.py command and expected outputs."
    )
    parser.add_argument("--source", required=True, help="directory containing raw WSI files")
    parser.add_argument("--save_dir", required=True, help="CLAM preprocessing output directory")
    parser.add_argument("--patch_size", type=positive_int, default=256, help="patch size at patch level")
    parser.add_argument("--step_size", type=positive_int, default=256, help="patch stride at patch level")
    parser.add_argument("--patch_level", type=nonnegative_int, default=0, help="OpenSlide level for patch coordinates")
    parser.add_argument("--preset", help="preset CSV name, for example bwh_biopsy.csv")
    parser.add_argument("--process_list", help="process-list filename inside save_dir")
    parser.add_argument("--seg", action="store_true", help="include segmentation/mask generation")
    parser.add_argument("--patch", action="store_true", help="include coordinate .h5 patch generation")
    parser.add_argument("--stitch", action="store_true", help="include stitch QC image generation")
    parser.add_argument(
        "--no_auto_skip",
        action="store_true",
        help="reprocess slides even when patches/<slide_id>.h5 already exists",
    )
    args = parser.parse_args()

    if not (args.seg or args.patch or args.stitch):
        parser.error("choose at least one stage: --seg, --patch, or --stitch")
    if args.process_list and any(sep in args.process_list for sep in ("/", "\\")):
        parser.error("--process_list should be a filename resolved inside --save_dir")
    if args.preset and args.preset not in PRESET_CHOICES:
        print(f"Note: preset {args.preset!r} is custom; ensure CLAM can find that CSV when running.")
    if args.step_size > args.patch_size:
        print("Note: step_size is larger than patch_size, so sampled patches will have gaps.")
    if args.step_size < args.patch_size:
        print("Note: step_size is smaller than patch_size, so sampled patches will overlap.")

    command = build_command(args)
    print("Command:")
    print(quote_command(command))
    print("\nExpected outputs under save_dir:")
    for path in output_layout(args.save_dir):
        print(f"- {path}")
    print("\nSkip behavior:")
    if args.no_auto_skip:
        print("- Existing patches/<slide_id>.h5 files will not trigger the default auto-skip.")
    else:
        print("- Existing patches/<slide_id>.h5 files are skipped by default and marked already_exist.")
    print("\nSafety:")
    print("- This helper only prints commands; it does not import CLAM/OpenSlide or read WSI files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
