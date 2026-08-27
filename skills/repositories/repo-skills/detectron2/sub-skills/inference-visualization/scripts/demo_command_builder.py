#!/usr/bin/env python3
"""Build and validate a Detectron2 demo-style command without running inference.

This helper mirrors the useful flags from Detectron2's demo entry point while
remaining safe for generated skills: it does not import detectron2, open images,
access webcams, load checkpoints, download weights, or execute the command.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Iterable, Sequence


MODE_FLAGS = ("input", "video_input", "webcam")


def _positive_threshold(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("threshold must be a number") from exc
    if not 0.0 <= parsed <= 1.0:
        raise argparse.ArgumentTypeError("threshold must be between 0 and 1")
    return parsed


def _validate_opts(opts: Sequence[str]) -> list[str]:
    if not opts:
        return []
    if len(opts) % 2 != 0:
        raise argparse.ArgumentTypeError(
            "--opts must contain Yacs-style KEY VALUE pairs, e.g. MODEL.DEVICE cpu"
        )
    return list(opts)


def _mode_count(args: argparse.Namespace) -> int:
    return sum(bool(getattr(args, name)) for name in MODE_FLAGS)


def _quote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def build_command(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if _mode_count(args) != 1:
        errors.append("choose exactly one input mode: --input, --video-input, or --webcam")

    if args.webcam and args.output:
        errors.append("webcam mode in the reference demo does not support --output")

    if args.input and len(args.input) > 1 and args.output:
        output_path = Path(args.output)
        if output_path.suffix:
            errors.append("multiple --input images require --output to be a directory, not a file")

    if args.video_input and args.output:
        output_path = Path(args.output)
        if output_path.exists() and output_path.is_file():
            errors.append("video --output points to an existing file; choose a new file or directory")

    opts = _validate_opts(args.opts)
    if any(item == "MODEL.DEVICE" for item in opts):
        device_value = opts[opts.index("MODEL.DEVICE") + 1]
        if device_value.startswith("cuda"):
            warnings.append("CUDA device requested; confirm CUDA is available before running")
    else:
        warnings.append("no MODEL.DEVICE override supplied; config default decides CPU/CUDA")

    if any(item == "MODEL.WEIGHTS" for item in opts):
        weights_value = opts[opts.index("MODEL.WEIGHTS") + 1]
        if weights_value.startswith(("detectron2://", "http://", "https://")):
            warnings.append("weights look remote; running may download files")
    else:
        warnings.append("no MODEL.WEIGHTS override supplied; config must define usable weights")

    command = [args.python, args.demo_script, "--config-file", args.config_file]
    if args.input:
        command.append("--input")
        command.extend(args.input)
    if args.video_input:
        command.extend(["--video-input", args.video_input])
    if args.webcam:
        command.append("--webcam")
    if args.output:
        command.extend(["--output", args.output])
    command.extend(["--confidence-threshold", str(args.confidence_threshold)])
    if opts:
        command.append("--opts")
        command.extend(opts)

    return command, errors + [f"warning: {message}" for message in warnings]


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and print a Detectron2 demo-style command without executing it."
    )
    parser.add_argument("--config-file", required=True, help="Config file path or model-zoo config path.")
    parser.add_argument("--input", nargs="+", help="One or more input images, or one glob pattern.")
    parser.add_argument("--video-input", help="Path to a video file.")
    parser.add_argument("--webcam", action="store_true", help="Use webcam mode.")
    parser.add_argument("--output", help="Output image file, output directory, or video file path.")
    parser.add_argument(
        "--confidence-threshold",
        default=0.5,
        type=_positive_threshold,
        help="Prediction display threshold between 0 and 1.",
    )
    parser.add_argument(
        "--demo-script",
        default="demo.py",
        help="Demo wrapper path to place in the printed command. This helper does not run it.",
    )
    parser.add_argument(
        "--python",
        default="python",
        help="Python executable token to place in the printed command.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON object with command, shell_command, issues, and ok fields.",
    )
    parser.add_argument(
        "--opts",
        nargs="*",
        default=[],
        help="Optional Yacs KEY VALUE overrides such as MODEL.DEVICE cpu.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)

    try:
        command, issues = build_command(args)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    errors = [issue for issue in issues if not issue.startswith("warning:")]
    payload = {
        "ok": not errors,
        "command": command,
        "shell_command": _quote_command(command),
        "issues": issues,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(payload["shell_command"])
        for issue in issues:
            print(issue, file=sys.stderr)

    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
