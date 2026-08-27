#!/usr/bin/env python3
"""Plan an OpenLLM BentoCloud deploy command without contacting BentoCloud.

Examples:
  python plan_deploy_command.py llama3.2:1b --env HF_TOKEN --instance-type gpu.a100
  python plan_deploy_command.py llama3.2:1b --require-env HF_TOKEN --shell

Secret safety: literal values in --env NAME=value are redacted in output.
This helper does not log into BentoCloud, query instance types, or deploy.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict
from shlex import quote


@dataclass
class DeployPlan:
    command: list[str]
    redacted_shell: str
    provided_env_names: list[str]
    missing_required_env: list[str]
    notes: list[str]


def env_name(item: str) -> str:
    return item.split("=", 1)[0]


def redact_env(item: str) -> str:
    if "=" in item:
        name, _value = item.split("=", 1)
        return f"{name}=<redacted>"
    return item


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", help="Model tag to deploy, for example llama3.2:1b.")
    parser.add_argument("--instance-type", help="BentoCloud instance type.")
    parser.add_argument("--repo", help="OpenLLM repo alias.")
    parser.add_argument("--context", help="BentoCloud context name.")
    parser.add_argument("--env", action="append", default=[], metavar="NAME[=VALUE]", help="Environment variable to pass. May be repeated.")
    parser.add_argument("--arg", action="append", default=[], metavar="KEY=VALUE", help="Bento argument to pass. May be repeated.")
    parser.add_argument("--require-env", action="append", default=[], metavar="NAME", help="Expected required env name. May be repeated.")
    parser.add_argument("--shell", action="store_true", help="Print only the redacted shell command.")
    return parser


def build_plan(args: argparse.Namespace) -> DeployPlan:
    command = ["openllm", "deploy", args.model]
    if args.instance_type:
        command += ["--instance-type", args.instance_type]
    if args.repo:
        command += ["--repo", args.repo]
    if args.context:
        command += ["--context", args.context]
    provided_names = []
    redacted_command = list(command)
    for item in args.env:
        provided_names.append(env_name(item))
        command += ["--env", item]
        redacted_command += ["--env", redact_env(item)]
    for item in args.arg:
        command += ["--arg", item]
        redacted_command += ["--arg", item]

    missing = [name for name in args.require_env if name not in provided_names and not os.environ.get(name)]
    notes = []
    if any("=" in item for item in args.env):
        notes.append("literal --env NAME=value input was redacted in output")
    if missing:
        notes.append("required env names are missing from --env and current environment")

    return DeployPlan(
        command=redacted_command,
        redacted_shell=" ".join(quote(part) for part in redacted_command),
        provided_env_names=sorted(set(provided_names)),
        missing_required_env=missing,
        notes=notes,
    )


def main() -> int:
    args = build_parser().parse_args()
    plan = build_plan(args)
    if args.shell:
        print(plan.redacted_shell)
        if plan.notes:
            for note in plan.notes:
                print(f"# note: {note}")
    else:
        print(json.dumps(asdict(plan), indent=2, sort_keys=False))
    return 2 if plan.missing_required_env else 0


if __name__ == "__main__":
    raise SystemExit(main())
