#!/usr/bin/env python3
"""Validate zi2zi inference, interpolation, and export command plans.

This helper does not run TensorFlow. It checks that the requested checkpoint,
source object, embedding IDs, and output paths are plausible and prints the
legacy zi2zi command a future agent should run.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List


def parse_ids(value: str) -> List[int]:
    ids: List[int] = []
    for part in value.split(","):
        if not part:
            continue
        ids.append(int(part))
    return ids


def format_command(parts: List[str]) -> str:
    return " ".join(str(part) for part in parts)


def infer_command(args: argparse.Namespace, embedding_ids: List[int]) -> List[str]:
    cmd = [
        args.python_bin,
        "infer.py",
        f"--model_dir={args.model_dir}",
        f"--batch_size={args.batch_size}",
        f"--source_obj={args.source_obj}",
        f"--embedding_ids={','.join(map(str, embedding_ids))}",
        f"--save_dir={args.save_dir}",
        f"--inst_norm={args.inst_norm}",
    ]
    if args.mode == "interpolate":
        cmd.append("--interpolate=1")
        cmd.append(f"--steps={args.steps}")
        if args.output_gif:
            cmd.append(f"--output_gif={args.output_gif}")
        if args.uroboros:
            cmd.append("--uroboros=1")
    return cmd


def export_command(args: argparse.Namespace) -> List[str]:
    return [
        args.python_bin,
        "export.py",
        f"--model_dir={args.model_dir}",
        f"--batch_size={args.batch_size}",
        f"--inst_norm={args.inst_norm}",
        f"--save_dir={args.save_dir}",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan zi2zi inference, interpolation, or export commands")
    sub = parser.add_subparsers(dest="mode", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--model-dir", required=True)
    common.add_argument("--batch-size", type=int, default=16)
    common.add_argument("--inst-norm", type=int, default=0)
    common.add_argument("--save-dir", required=True)
    common.add_argument("--python-bin", default="python")
    common.add_argument("--check-paths", action="store_true")
    common.add_argument("--json", action="store_true", help="Emit JSON report")

    infer_p = sub.add_parser("infer", parents=[common])
    infer_p.add_argument("--source-obj", required=True)
    infer_p.add_argument("--embedding-ids", required=True)

    interp_p = sub.add_parser("interpolate", parents=[common])
    interp_p.add_argument("--source-obj", required=True)
    interp_p.add_argument("--embedding-ids", required=True)
    interp_p.add_argument("--steps", type=int, default=10)
    interp_p.add_argument("--output-gif")
    interp_p.add_argument("--uroboros", action="store_true")

    export_p = sub.add_parser("export", parents=[common])

    args = parser.parse_args()

    problems: List[str] = []
    warnings: List[str] = []

    if args.batch_size <= 0:
        problems.append("--batch-size must be positive")
    if args.inst_norm not in (0, 1):
        problems.append("--inst-norm must be 0 or 1")

    model_dir = Path(args.model_dir)
    save_dir = Path(args.save_dir)
    if args.check_paths:
        if not model_dir.exists():
            problems.append(f"missing model directory: {model_dir}")
        if args.mode != "export":
            source_obj = Path(args.source_obj)
            if not source_obj.exists():
                problems.append(f"missing source object: {source_obj}")
        if save_dir.exists() and not save_dir.is_dir():
            problems.append(f"save dir exists but is not a directory: {save_dir}")

    if args.mode == "export":
        command = export_command(args)
        summary = {"mode": args.mode, "command": format_command(command)}
    else:
        embedding_ids = parse_ids(args.embedding_ids)
        if not embedding_ids:
            problems.append("at least one embedding id is required")
            embedding_ids = []
        if args.mode == "interpolate":
            if len(embedding_ids) < 2:
                problems.append("interpolation requires at least two embedding ids")
            if args.steps <= 0:
                problems.append("--steps must be positive")
        if args.mode == "infer" and len(embedding_ids) > 1:
            warnings.append("multiple embedding ids enable random style selection per batch")
        command = infer_command(args, embedding_ids)
        summary = {"mode": args.mode, "command": format_command(command), "embedding_ids": embedding_ids}
        if args.mode == "interpolate":
            summary["uroboros"] = bool(args.uroboros)
            if args.output_gif:
                summary["output_gif"] = args.output_gif

    summary["problems"] = problems
    summary["warnings"] = warnings
    summary["paths_checked"] = bool(args.check_paths)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("# zi2zi inference/export plan\n")
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
        print("## Command")
        print(summary["command"])
        if args.mode != "export":
            print(f"\n## Embedding IDs\n{summary['embedding_ids']}")
    return 2 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
