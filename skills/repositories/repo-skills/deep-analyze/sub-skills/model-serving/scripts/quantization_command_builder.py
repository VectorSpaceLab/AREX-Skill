#!/usr/bin/env python3
"""Print a dry-run DeepAnalyze quantization command.

The script never imports bitsandbytes or mutates a checkpoint. It only renders
command text based on the requested quantization profile.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys


def render_shell_command(args: list[str]) -> str:
    if not args:
        return ""
    lines = [shlex.quote(args[0])]
    for arg in args[1:]:
        lines.append(f"  {shlex.quote(arg)}")
    separator = " " + "\\" + "\n"
    return separator.join(lines)


def build_plan(ns: argparse.Namespace) -> dict:
    command = [
        ns.python,
        "quantize.py",
        "--model_path",
        ns.model_path,
        "--output_dir",
        ns.output_dir,
        "--quant_type",
        ns.quant_type,
    ]
    if ns.no_double_quant:
        command.append("--no_double_quant")
    if ns.extra_arg:
        for item in ns.extra_arg:
            command.append(item)

    outputs = []
    if ns.quant_type in {"4bit", "both"}:
        outputs.append(f"{ns.output_dir}/4bit")
    if ns.quant_type in {"8bit", "both"}:
        outputs.append(f"{ns.output_dir}/8bit")

    return {
        "source_script": "quantize.py",
        "quant_type": ns.quant_type,
        "double_quant": not ns.no_double_quant,
        "outputs": outputs,
        "command": command,
        "shell": render_shell_command(command),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a dry-run DeepAnalyze quantization command."
    )
    parser.add_argument("--model-path", required=True, help="Path to the source checkpoint.")
    parser.add_argument("--output-dir", required=True, help="Directory for the quantized copy.")
    parser.add_argument(
        "--quant-type",
        choices=["4bit", "8bit", "both"],
        default="both",
        help="Quantization profile to render.",
    )
    parser.add_argument(
        "--no-double-quant",
        action="store_true",
        help="Mirror the source script flag for 4-bit output.",
    )
    parser.add_argument("--python", default="python", help="Python executable to print in the command.")
    parser.add_argument(
        "--extra-arg",
        action="append",
        default=[],
        help="Append an extra raw argument to the rendered command.",
    )
    parser.add_argument("--json", action="store_true", help="Print structured JSON instead of a shell block.")
    return parser.parse_args()


def main() -> int:
    ns = parse_args()
    plan = build_plan(ns)

    if ns.json:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0

    print(f"Quantization type: {plan['quant_type']}")
    print(f"Double quantization: {'enabled' if plan['double_quant'] else 'disabled'}")
    print(f"Expected outputs: {', '.join(plan['outputs']) if plan['outputs'] else 'none'}")
    print("\nDry-run command:\n")
    print(plan["shell"])
    print("\nNote: this script only prints a command; it does not mutate a checkpoint.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
