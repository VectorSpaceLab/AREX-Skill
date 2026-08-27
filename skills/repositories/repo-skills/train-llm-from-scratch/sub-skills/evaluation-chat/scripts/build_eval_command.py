#!/usr/bin/env python3
"""Dry-run command builder for train-llm-from-scratch GSM8K evaluation.

The script prints commands only. It does not load checkpoints, import torch,
open datasets, create output files, or execute the repo evaluator.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Stage:
    label: str
    ckpt: str


def shell_words(words: list[str]) -> str:
    return " ".join(shlex.quote(str(w)) for w in words)


def python_words(python: str) -> list[str]:
    parts = shlex.split(python)
    return parts or ["python"]


def parse_stage(raw: str) -> Stage:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("stage must be LABEL=CHECKPOINT_PATH")
    label, ckpt = raw.split("=", 1)
    label, ckpt = label.strip(), ckpt.strip()
    if not label or not ckpt:
        raise argparse.ArgumentTypeError("stage label and checkpoint path must be non-empty")
    return Stage(label=label, ckpt=ckpt)


def eval_command(args: argparse.Namespace, stage: Stage) -> str:
    cmd = ["PYTHONPATH=.", *python_words(args.python), "scripts/eval_post_training.py"]
    cmd += ["--ckpt", stage.ckpt, "--label", stage.label]
    cmd += ["--limit", str(args.limit), "--split", args.split]
    cmd += ["--max_new_tokens", str(args.max_new_tokens)]
    if args.device:
        cmd += ["--device", args.device]
    cmd += ["--samples", str(args.samples)]
    if args.append:
        cmd += ["--append", args.append]
    return shell_words(cmd)


def table_command(args: argparse.Namespace, table_path: str) -> str:
    cmd = ["PYTHONPATH=.", *python_words(args.python), "scripts/eval_post_training.py", "--table", table_path]
    return shell_words(cmd)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Print dry-run PYTHONPATH=. python scripts/eval_post_training.py commands "
            "for one checkpoint, repeated stage rows, or table rendering."
        )
    )
    p.add_argument("--ckpt", help="single checkpoint path to evaluate")
    p.add_argument("--label", default="model", help="label for --ckpt row (default: model)")
    p.add_argument(
        "--stage",
        action="append",
        type=parse_stage,
        default=[],
        metavar="LABEL=CKPT",
        help="stage row to evaluate; repeat for Base/SFT/DPO/PPO/GRPO table construction",
    )
    p.add_argument("--limit", type=int, default=200, help="GSM8K example limit (default: 200)")
    p.add_argument("--split", default="test", help="GSM8K split (default: test)")
    p.add_argument("--max_new_tokens", type=int, default=300, help="generation budget per question (default: 300)")
    p.add_argument("--device", default=None, help="device to pass through, e.g. cuda or cpu")
    p.add_argument("--samples", type=int, default=3, help="sample generations to print (default: 3)")
    p.add_argument("--append", help="JSONL file for appending result rows")
    p.add_argument("--table", help="existing JSONL table to render and exit")
    p.add_argument(
        "--render-table",
        action="store_true",
        help="after emitted eval rows, also print a --table command for the append file",
    )
    p.add_argument("--python", default="python", help="python executable command to print (default: python)")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.limit < 0:
        parser.error("--limit must be non-negative")
    if args.max_new_tokens <= 0:
        parser.error("--max_new_tokens must be positive")
    if args.samples < 0:
        parser.error("--samples must be non-negative")

    if args.table:
        if args.ckpt or args.stage:
            parser.error("--table renders an existing JSONL; do not combine it with --ckpt or --stage")
        print("# dry run: render an existing stage table")
        print(table_command(args, args.table))
        return 0

    stages: list[Stage] = []
    if args.ckpt:
        stages.append(Stage(label=args.label, ckpt=args.ckpt))
    stages.extend(args.stage)

    if not stages:
        parser.error("provide --ckpt, repeated --stage LABEL=CKPT, or --table PATH")

    print("# dry run: GSM8K evaluation commands (not executed)")
    if args.stage and not args.append:
        print("# note: repeated --stage rows usually need --append PATH to build one JSONL table")
    for stage in stages:
        print(eval_command(args, stage))

    if args.render_table:
        if not args.append:
            parser.error("--render-table requires --append PATH")
        print(table_command(args, args.append))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
