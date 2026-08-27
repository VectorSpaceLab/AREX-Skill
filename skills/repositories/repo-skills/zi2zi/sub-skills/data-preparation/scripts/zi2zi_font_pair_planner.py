#!/usr/bin/env python3
"""Plan zi2zi font-to-image and packaging commands safely.

The original renderer is a Python 2 script. This helper is a Python 3 planner:
it validates labels and optional paths, then prints command templates for the
user's zi2zi checkout. It does not render fonts or write training data.
"""
from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Dict, List, Tuple

BUILTIN_CHARSETS = {"CN", "CN_T", "JP", "KR"}


def parse_target(value: str) -> Tuple[int, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("target font must be LABEL=PATH")
    label_text, path = value.split("=", 1)
    try:
        label = int(label_text)
    except ValueError:
        raise argparse.ArgumentTypeError("target label must be an integer")
    if label < 0:
        raise argparse.ArgumentTypeError("target label must be non-negative")
    if not path:
        raise argparse.ArgumentTypeError("target font path must be non-empty")
    return label, path


def q(value: object) -> str:
    return shlex.quote(str(value))


def build_font2img_command(args: argparse.Namespace, label: int, dst_font: str) -> List[str]:
    return [
        args.python_bin,
        "font2img.py",
        f"--src_font={args.src_font}",
        f"--dst_font={dst_font}",
        f"--charset={args.charset}",
        f"--sample_count={args.sample_count}",
        f"--sample_dir={args.sample_root}",
        f"--label={label}",
        f"--filter={int(args.filter)}",
        f"--shuffle={int(args.shuffle)}",
        f"--char_size={args.char_size}",
        f"--canvas_size={args.canvas_size}",
        f"--x_offset={args.x_offset}",
        f"--y_offset={args.y_offset}",
    ]


def shell_join(parts: List[str]) -> str:
    return " ".join(q(part) for part in parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan zi2zi font rendering and packaging commands")
    parser.add_argument("--src-font", required=True, help="Source/base font path for the right half of each pair.")
    parser.add_argument(
        "--target-font",
        action="append",
        required=True,
        type=parse_target,
        metavar="LABEL=PATH",
        help="Target/style font with integer label. Repeat for multiple styles.",
    )
    parser.add_argument("--charset", default="CN", help="CN, CN_T, JP, KR, or a one-line custom charset file.")
    parser.add_argument("--sample-count", type=int, default=1000)
    parser.add_argument("--sample-root", default="samples")
    parser.add_argument("--package-save-dir", default="experiment/data")
    parser.add_argument("--split-ratio", type=float, default=0.1)
    parser.add_argument("--filter", type=int, choices=[0, 1], default=1)
    parser.add_argument("--shuffle", type=int, choices=[0, 1], default=1)
    parser.add_argument("--char-size", type=int, default=150)
    parser.add_argument("--canvas-size", type=int, default=256)
    parser.add_argument("--x-offset", type=int, default=20)
    parser.add_argument("--y-offset", type=int, default=20)
    parser.add_argument("--python-bin", default="python", help="Python executable for original zi2zi scripts.")
    parser.add_argument("--check-paths", action="store_true", help="Check that font and custom charset paths exist.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of shell text.")
    args = parser.parse_args()

    labels = [label for label, _ in args.target_font]
    duplicate_labels = sorted({label for label in labels if labels.count(label) > 1})
    problems: List[str] = []
    warnings: List[str] = []

    if duplicate_labels:
        problems.append("duplicate target labels: " + ", ".join(map(str, duplicate_labels)))
    if args.sample_count <= 0:
        problems.append("--sample-count must be positive")
    if not 0.0 <= args.split_ratio <= 1.0:
        problems.append("--split-ratio must be between 0 and 1")
    if args.charset not in BUILTIN_CHARSETS and args.check_paths and not Path(args.charset).exists():
        problems.append(f"custom charset file does not exist: {args.charset}")
    if args.check_paths:
        if not Path(args.src_font).exists():
            problems.append(f"source font does not exist: {args.src_font}")
        for _, path in args.target_font:
            if not Path(path).exists():
                problems.append(f"target font does not exist: {path}")
    if args.filter == 1 and args.sample_count < 10:
        warnings.append("filtering can dominate tiny smoke tests; consider --filter=0 for a tiny custom charset")

    render_commands = [build_font2img_command(args, label, path) for label, path in args.target_font]
    package_command = [
        args.python_bin,
        "package.py",
        f"--dir={args.sample_root}",
        f"--save_dir={args.package_save_dir}",
        f"--split_ratio={args.split_ratio}",
    ]

    report: Dict[str, object] = {
        "labels": labels,
        "embedding_num_minimum": max(labels) + 1 if labels else 0,
        "render_commands": [shell_join(command) for command in render_commands],
        "package_command": shell_join(package_command),
        "expected_pair_size": [args.canvas_size * 2, args.canvas_size],
        "expected_files": ["train.obj", "val.obj"],
        "warnings": warnings,
        "problems": problems,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("# zi2zi preprocessing command plan\n")
        if problems:
            print("## Problems to fix before running")
            for problem in problems:
                print(f"- {problem}")
            print()
        if warnings:
            print("## Warnings")
            for warning in warnings:
                print(f"- {warning}")
            print()
        print("## Create directories")
        print(f"mkdir -p {q(args.sample_root)} {q(args.package_save_dir)}\n")
        print("## Render commands")
        for command in report["render_commands"]:  # type: ignore[index]
            print(command)
        print("\n## Package command")
        print(report["package_command"])
        print("\n## Training note")
        print(f"Use --embedding_num={report['embedding_num_minimum']} or larger for these labels.")

    return 2 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
