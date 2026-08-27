#!/usr/bin/env python3
"""Print a dry-run tokenizer tag-extension plan for DeepAnalyze.

The script never loads a checkpoint. It only prints the fixed tag list and the
command text for the source helper.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys

DEFAULT_TAGS = [
    "<Analyze>",
    "</Analyze>",
    "<Understand>",
    "</Understand>",
    "<Code>",
    "</Code>",
    "<Execute>",
    "</Execute>",
    "<Answer>",
    "</Answer>",
]


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
        "deepanalyze/add_vocab.py",
        "--model_path",
        ns.model_path,
        "--save_path",
        ns.save_path,
        "--add_tags",
    ]
    if ns.extra_arg:
        for item in ns.extra_arg:
            command.append(item)

    return {
        "model_path": ns.model_path,
        "save_path": ns.save_path,
        "base_model_name": ns.base_model_name,
        "tag_count": len(DEFAULT_TAGS),
        "tags": DEFAULT_TAGS,
        "command": command,
        "shell": render_shell_command(command),
        "pre_training_step": ns.base_model_name == "DeepSeek-R1-0528-Qwen3-8B",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a dry-run DeepAnalyze tokenizer tag-extension plan."
    )
    parser.add_argument("--model-path", required=True, help="Base checkpoint directory.")
    parser.add_argument("--save-path", required=True, help="Output directory for the extended copy.")
    parser.add_argument(
        "--base-model-name",
        default="DeepSeek-R1-0528-Qwen3-8B",
        help="Used for the pre-training reminder in the summary.",
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

    print(f"Base model: {plan['base_model_name']}")
    print(f"Tag count: {plan['tag_count']}")
    print("Tags:")
    for tag in plan["tags"]:
        print(f"  - {tag}")
    print(f"Pre-training step: {'yes' if plan['pre_training_step'] else 'no'}")
    print("\nDry-run command:\n")
    print(plan["shell"])
    print("\nNote: this script only prints a command; it does not extend a checkpoint.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
