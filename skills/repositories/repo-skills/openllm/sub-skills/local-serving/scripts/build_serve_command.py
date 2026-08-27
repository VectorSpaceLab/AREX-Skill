#!/usr/bin/env python3
"""Build a safe OpenLLM local-serving command without starting a model.

Examples:
  python build_serve_command.py serve llama3.2:1b --port 3000 --env HF_TOKEN --arg device=cuda
  python build_serve_command.py run llama3:8b --timeout 600 --shell

This helper does not download weights, update repositories, or launch BentoML.
It only normalizes user intent into a command preview plus forwarded env/arg data.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from shlex import quote
from typing import Any


@dataclass
class PlannedCommand:
    mode: str
    model: str
    repo: str | None
    port: int | None
    timeout: int | None
    env: list[str]
    arg: list[str]
    command: list[str]


def parse_key_value(text: str) -> str:
    if not text:
        raise argparse.ArgumentTypeError("value must not be empty")
    return text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["serve", "run"], help="Which OpenLLM command to plan.")
    parser.add_argument("model", help="Model tag such as llama3.2:1b.")
    parser.add_argument("--repo", help="Repository alias to pass to OpenLLM.")
    parser.add_argument("--port", type=int, help="Port to pass to OpenLLM.")
    parser.add_argument("--timeout", type=int, help="Timeout for run mode.")
    parser.add_argument(
        "--env",
        action="append",
        default=[],
        metavar="NAME[=VALUE]",
        help="Environment variable to forward. May be repeated.",
    )
    parser.add_argument(
        "--arg",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Bento argument to forward. May be repeated.",
    )
    parser.add_argument(
        "--shell",
        action="store_true",
        help="Render the planned command as a shell-quoted string instead of JSON.",
    )
    return parser


def build_command(args: argparse.Namespace) -> PlannedCommand:
    command = ["openllm", args.mode, args.model]
    if args.repo:
        command += ["--repo", args.repo]
    if args.port is not None:
        command += ["--port", str(args.port)]
    if args.mode == "run" and args.timeout is not None:
        command += ["--timeout", str(args.timeout)]
    for item in args.env:
        command += ["--env", item]
    for item in args.arg:
        command += ["--arg", item]
    return PlannedCommand(
        mode=args.mode,
        model=args.model,
        repo=args.repo,
        port=args.port,
        timeout=args.timeout if args.mode == "run" else None,
        env=list(args.env),
        arg=list(args.arg),
        command=command,
    )


def render_shell(planned: PlannedCommand) -> str:
    return " ".join(quote(part) for part in planned.command)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    planned = build_command(args)
    if args.shell:
        print(render_shell(planned))
    else:
        print(json.dumps(asdict(planned), indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
