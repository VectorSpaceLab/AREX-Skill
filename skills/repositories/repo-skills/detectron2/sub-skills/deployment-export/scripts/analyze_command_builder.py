#!/usr/bin/env python3
"""Build safe Detectron2 model-analysis commands without executing them."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path
from typing import Iterable, List


TASK_NOTES = {
    "flop": "Data-dependent FLOP analysis; needs valid test data and usually weights.",
    "activation": "Data-dependent activation analysis; can be memory-heavy and needs valid test data.",
    "parameter": "Static parameter-count table; safest analysis task.",
    "structure": "Static model structure printout; useful before export.",
}

DATA_DEPENDENT_TASKS = {"flop", "activation"}


def quote_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts if str(part) != "")


def split_override(text: str, style: str) -> List[str]:
    if style == "yacs":
        if "=" in text:
            key, value = text.split("=", 1)
            if not key or value == "":
                raise argparse.ArgumentTypeError(f"Invalid Yacs override {text!r}; expected KEY=VALUE or 'KEY VALUE'.")
            return [key, value]
        parts = text.strip().split(None, 1)
        if len(parts) != 2:
            raise argparse.ArgumentTypeError(f"Invalid Yacs override {text!r}; expected KEY=VALUE or 'KEY VALUE'.")
        return parts
    if "=" not in text:
        raise argparse.ArgumentTypeError(f"Invalid LazyConfig override {text!r}; expected path.key=value.")
    return [text]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit a Detectron2 model-analysis command without running analysis."
    )
    parser.add_argument("--config-file", required=True, help="Config file path for the real analysis command.")
    parser.add_argument(
        "--tasks",
        nargs="+",
        choices=sorted(TASK_NOTES),
        required=True,
        help="One or more analysis tasks.",
    )
    parser.add_argument(
        "--num-inputs",
        type=int,
        default=100,
        help="Number of inputs for data-dependent flop/activation analysis.",
    )
    parser.add_argument(
        "--style",
        choices=["auto", "yacs", "lazy"],
        default="auto",
        help="Override syntax style. Auto infers LazyConfig for .py and Yacs otherwise.",
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        help="Config override. Yacs accepts KEY=VALUE or 'KEY VALUE'; LazyConfig requires path.key=value.",
    )
    parser.add_argument("--python", default="python", help="Python executable placeholder to print.")
    parser.add_argument(
        "--script",
        default="ANALYZE_DRIVER.py",
        help="Analysis driver path to print in the command preview.",
    )
    return parser.parse_args()


def infer_style(args: argparse.Namespace) -> str:
    if args.style != "auto":
        return args.style
    return "lazy" if Path(args.config_file).suffix.lower() == ".py" else "yacs"


def validate_args(args: argparse.Namespace, style: str) -> List[str]:
    warnings: List[str] = []
    tasks = set(args.tasks)
    if args.num_inputs <= 0:
        raise SystemExit("--num-inputs must be positive.")

    if DATA_DEPENDENT_TASKS & tasks:
        warnings.append("FLOP/activation tasks build a test loader and iterate over data; confirm dataset registration and availability before running.")
        if not any("WEIGHTS" in item or "init_checkpoint" in item for item in args.override):
            warnings.append("No obvious weights/checkpoint override was supplied; confirm the config already points to intended weights.")
    else:
        warnings.append("Only static tasks were selected; weights and datasets are usually not required, but the model is still built.")

    if style == "yacs" and Path(args.config_file).suffix.lower() == ".py":
        warnings.append("Yacs style was selected for a .py config; LazyConfig may be intended.")
    if style == "lazy" and Path(args.config_file).suffix.lower() in {".yaml", ".yml"}:
        warnings.append("LazyConfig style was selected for a YAML config; Yacs may be intended.")

    if args.num_inputs > 100 and DATA_DEPENDENT_TASKS & tasks:
        warnings.append("Large --num-inputs values can make analysis slow; use a small sample first.")

    return warnings


def build_command(args: argparse.Namespace, style: str) -> List[str]:
    command = [args.python, args.script, "--config-file", args.config_file, "--tasks"]
    command.extend(args.tasks)
    if DATA_DEPENDENT_TASKS & set(args.tasks):
        command.extend(["--num-inputs", str(args.num_inputs)])
    for item in args.override:
        command.extend(split_override(item, style))
    return command


def main() -> int:
    args = parse_args()
    style = infer_style(args)
    warnings = validate_args(args, style)
    command = build_command(args, style)

    print("Analyze command preview (not executed):")
    print(quote_join(command))
    print("\nSelected tasks:")
    for task in args.tasks:
        print(f"- {task}: {TASK_NOTES[task]}")
    print(f"\nOverride style: {style}")
    if warnings:
        print("\nReview before running:")
        for warning in warnings:
            print(f"- {warning}")
    print("\nSafety: this helper only prints a command; it does not import detectron2, build models, load weights, or touch datasets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
