#!/usr/bin/env python3
"""Run a bounded headless SuperGlue demo on a directory of frames."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a short, headless demo_superglue smoke on a directory of frames."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        required=True,
        help="Repository root that contains demo_superglue.py.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory of frames to process with demo_superglue.py.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where rendered demo frames will be written.",
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Backend to use for the smoke run.",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=2,
        help="Maximum number of frames to process.",
    )
    parser.add_argument(
        "--resize",
        type=int,
        nargs="+",
        default=[320, 240],
        help=(
            "Resize arguments passed through to demo_superglue.py. Use one value for "
            "max-dimension resize, two values for exact width/height, or -1 to skip resize."
        ),
    )
    return parser


def normalize_resize(values: list[int]) -> list[int]:
    if len(values) == 2 and values[1] == -1:
        return values[:1]
    if len(values) in {1, 2}:
        return values
    raise SystemExit("--resize accepts one or two integers.")


def select_device(requested: str) -> str:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - environment failure
        raise SystemExit(f"Unable to import torch for backend selection: {exc}") from exc

    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but torch.cuda.is_available() is false.")
    return requested


def main() -> int:
    args = build_parser().parse_args()

    if args.max_length < 1:
        raise SystemExit("--max-length must be at least 1.")

    repo_root = args.repo_root.expanduser().resolve()
    input_dir = args.input_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()

    demo_script = repo_root / "demo_superglue.py"
    if not demo_script.is_file():
        raise SystemExit("demo_superglue.py was not found under the provided repo root.")
    if not input_dir.is_dir():
        raise SystemExit("--input-dir must point to an existing directory.")

    output_dir.mkdir(parents=True, exist_ok=True)

    resize = normalize_resize(list(args.resize))
    device = select_device(args.device)

    command = [
        sys.executable,
        str(demo_script),
        "--input",
        str(input_dir),
        "--output_dir",
        str(output_dir),
        "--no_display",
        "--max_length",
        str(args.max_length),
        "--resize",
        *[str(value) for value in resize],
    ]
    if device == "cpu":
        command.append("--force_cpu")

    print(f"Running headless demo smoke on {device}.")
    print(f"Bounded to {args.max_length} frame(s).")

    subprocess.run(command, cwd=str(repo_root), check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
