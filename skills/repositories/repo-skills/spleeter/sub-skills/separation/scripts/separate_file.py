#!/usr/bin/env python3
"""Safe wrapper for building and running `python -m spleeter separate`.

The helper validates local input files, keeps filename templates relative to the
chosen output directory, warns about common template collisions, and supports a
--dry-run mode that prints the command without executing Spleeter.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

CODECS = ("wav", "mp3", "ogg", "m4a", "wma", "flac")
DEFAULT_ADAPTER = "spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter"


def non_negative_float(value: str) -> float:
    """Parse a non-negative float argument."""
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a number, got {value!r}") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def positive_float(value: str) -> float:
    """Parse a positive float argument."""
    parsed = non_negative_float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate inputs and run, or dry-run, a `python -m spleeter separate` "
            "command for one or more audio files."
        )
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Input audio file(s). Files must already exist; use shell globbing for batches.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        "--output_path",
        dest="output_dir",
        default="separated_audio",
        help="Output directory passed to Spleeter as --output_path (default: separated_audio).",
    )
    parser.add_argument(
        "-p",
        "--params",
        "--params_filename",
        dest="params",
        default="spleeter:2stems",
        help="Spleeter params descriptor or JSON config path (default: spleeter:2stems).",
    )
    parser.add_argument(
        "-f",
        "--filename-format",
        "--filename_format",
        dest="filename_format",
        default="{filename}/{instrument}.{codec}",
        help=(
            "Output template using {filename}, {foldername}, {instrument}, and {codec} "
            "(default: {filename}/{instrument}.{codec})."
        ),
    )
    parser.add_argument(
        "-c",
        "--codec",
        choices=CODECS,
        default="wav",
        help="Output codec (default: wav).",
    )
    parser.add_argument(
        "-b",
        "--bitrate",
        default="128k",
        help="Output audio bitrate passed to Spleeter (default: 128k).",
    )
    parser.add_argument(
        "-s",
        "--offset",
        type=non_negative_float,
        default=0.0,
        help="Start offset in seconds (default: 0).",
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=positive_float,
        default=600.0,
        help="Maximum duration in seconds after offset (default: 600).",
    )
    parser.add_argument(
        "-a",
        "--adapter",
        default=DEFAULT_ADAPTER,
        help=f"AudioAdapter dotted class path (default: {DEFAULT_ADAPTER}).",
    )
    parser.add_argument(
        "--mwf",
        action="store_true",
        help="Enable multichannel Wiener filtering.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable Spleeter verbose logs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command and warnings without executing Spleeter.",
    )
    return parser


def validate_inputs(parser: argparse.ArgumentParser, inputs: Iterable[Path]) -> None:
    missing: List[str] = []
    not_files: List[str] = []
    for path in inputs:
        if not path.exists():
            missing.append(str(path))
        elif not path.is_file():
            not_files.append(str(path))
    if missing:
        parser.error("input file(s) not found: " + ", ".join(missing))
    if not_files:
        parser.error("input path(s) are not files: " + ", ".join(not_files))


def validate_template(parser: argparse.ArgumentParser, template: str) -> None:
    if os.path.isabs(template):
        parser.error("filename_format must be relative to the output directory")
    if ".." in Path(template).parts:
        parser.error("filename_format must not contain parent-directory '..' segments")


def template_warnings(template: str, input_count: int) -> List[str]:
    warnings: List[str] = []
    if "{instrument}" not in template:
        warnings.append(
            "filename_format does not include {instrument}; stems from one input may conflict"
        )
    if input_count > 1 and "{filename}" not in template and "{foldername}" not in template:
        warnings.append(
            "multiple inputs with no {filename} or {foldername}; later files may overwrite earlier outputs"
        )
    if "{codec}" not in template and not Path(template).suffix:
        warnings.append(
            "filename_format has no {codec} variable or literal extension; output codec may be unclear"
        )
    return warnings


def build_command(args: argparse.Namespace) -> List[str]:
    cmd: List[str] = [
        sys.executable,
        "-m",
        "spleeter",
        "separate",
        "--adapter",
        args.adapter,
        "--bitrate",
        args.bitrate,
        "--codec",
        args.codec,
        "--duration",
        str(args.duration),
        "--offset",
        str(args.offset),
        "--output_path",
        str(args.output_dir),
        "--filename_format",
        args.filename_format,
        "--params_filename",
        args.params,
    ]
    if args.mwf:
        cmd.append("--mwf")
    if args.verbose:
        cmd.append("--verbose")
    cmd.extend(str(path) for path in args.inputs)
    return cmd


def display_command(cmd: List[str]) -> str:
    """Return a copy/paste-friendly command without exposing interpreter paths."""
    display = list(cmd)
    if len(display) >= 3 and display[1:3] == ["-m", "spleeter"]:
        display[0] = "python"
    return shlex.join(display)


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_inputs(parser, args.inputs)
    validate_template(parser, args.filename_format)

    warnings = template_warnings(args.filename_format, len(args.inputs))
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    cmd = build_command(args)
    print(display_command(cmd))
    if args.dry_run:
        return 0

    try:
        completed = subprocess.run(cmd, check=False)
    except FileNotFoundError as exc:
        print(f"failed to execute {cmd[0]!r}: {exc}", file=sys.stderr)
        return 127
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
