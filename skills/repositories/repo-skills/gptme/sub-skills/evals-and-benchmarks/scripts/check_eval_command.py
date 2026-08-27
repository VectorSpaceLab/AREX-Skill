#!/usr/bin/env python3
"""Build a safe dry-run gptme-eval command without executing anything.

This helper normalizes suite names, model specs, tool formats, Docker mode,
timeout, and parallelism into the exact shell command that should be run.

Examples:
    python scripts/check_eval_command.py hello -m anthropic/claude-sonnet-4-6
    python scripts/check_eval_command.py all-practical -m anthropic/claude-sonnet-4-6 --tool-format tool --use-docker
    python scripts/check_eval_command.py hello -m anthropic/claude-sonnet-4-6@xml --timeout 600 --parallel 4
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import dataclass
from typing import Any

TOOL_FORMATS = {"markdown", "xml", "tool"}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


@dataclass(frozen=True)
class ModelSpec:
    raw: str
    model: str
    tool_format: str | None

    @property
    def normalized(self) -> str:
        if self.tool_format:
            return f"{self.model}@{self.tool_format}"
        return self.model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a safe dry-run gptme-eval command without executing anything",
    )
    parser.add_argument(
        "suites",
        nargs="+",
        help="Suite names or aliases to run, such as hello, practical, all-practical, or all.",
    )
    parser.add_argument(
        "-m",
        "--model",
        action="append",
        required=True,
        help="Model spec to include. Repeat for multiple models. A suffix like @tool is allowed.",
    )
    parser.add_argument(
        "--tool-format",
        choices=sorted(TOOL_FORMATS),
        default=None,
        help="Apply one tool format to models that do not already include @format.",
    )
    parser.add_argument(
        "--use-docker",
        action="store_true",
        help="Add gptme-eval's Docker isolation flag.",
    )
    parser.add_argument(
        "--timeout",
        type=positive_int,
        default=300,
        help="Per-eval timeout in seconds.",
    )
    parser.add_argument(
        "--parallel",
        type=positive_int,
        default=10,
        help="Eval concurrency.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON object instead of a shell command.",
    )
    return parser.parse_args()


def parse_model_spec(raw: str, tool_format: str | None) -> ModelSpec:
    if "@" in raw:
        model, suffix = raw.rsplit("@", 1)
        if suffix in TOOL_FORMATS:
            return ModelSpec(raw=raw, model=model, tool_format=suffix)
    return ModelSpec(raw=raw, model=raw, tool_format=tool_format)


def build_command(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    notes: list[str] = []
    cmd = ["gptme-eval", *args.suites]
    for raw_model in args.model:
        spec = parse_model_spec(raw_model, args.tool_format)
        if spec.raw != spec.normalized and spec.tool_format and "@" not in raw_model:
            notes.append(f"applied --tool-format {spec.tool_format} to {raw_model}")
        cmd.extend(["--model", spec.normalized])
    if args.use_docker:
        cmd.append("--use-docker")
    cmd.extend(["--timeout", str(args.timeout), "--parallel", str(args.parallel)])
    return cmd, notes


def as_json(args: argparse.Namespace, cmd: list[str], notes: list[str]) -> dict[str, Any]:
    parsed_models = [parse_model_spec(raw, args.tool_format).normalized for raw in args.model]
    return {
        "command": cmd,
        "shell": shlex.join(cmd),
        "suites": list(args.suites),
        "models": parsed_models,
        "tool_format": args.tool_format,
        "use_docker": args.use_docker,
        "timeout": args.timeout,
        "parallel": args.parallel,
        "notes": notes,
    }


def main() -> int:
    args = parse_args()
    cmd, notes = build_command(args)
    if args.json:
        print(json.dumps(as_json(args, cmd, notes), indent=2))
    else:
        print(shlex.join(cmd))
        for note in notes:
            print(f"# {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
