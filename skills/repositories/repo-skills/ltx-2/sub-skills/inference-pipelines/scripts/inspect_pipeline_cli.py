#!/usr/bin/env python3
"""Safely inspect LTX-2 pipeline CLI help.

This helper only lists known ltx_pipelines modules, prints the help command, or
executes ``python -m <known_module> --help``. It never forwards generation
arguments and never downloads models.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from collections import OrderedDict

MODULES: "OrderedDict[str, str]" = OrderedDict(
    [
        ("distilled", "ltx_pipelines.distilled"),
        ("ti2vid_two_stages", "ltx_pipelines.ti2vid_two_stages"),
        ("ti2vid_two_stages_hq", "ltx_pipelines.ti2vid_two_stages_hq"),
        ("ti2vid_one_stage", "ltx_pipelines.ti2vid_one_stage"),
        ("ic_lora", "ltx_pipelines.ic_lora"),
        ("keyframe_interpolation", "ltx_pipelines.keyframe_interpolation"),
        ("a2vid_two_stage", "ltx_pipelines.a2vid_two_stage"),
        ("retake", "ltx_pipelines.retake"),
        ("hdr_ic_lora", "ltx_pipelines.hdr_ic_lora"),
        ("dubit", "ltx_pipelines.dubit"),
        ("t2a_one_stage", "ltx_pipelines.t2a_one_stage"),
        ("dfr_pipeline", "ltx_pipelines.dfr_pipeline"),
    ]
)

ALIASES = dict(MODULES)
ALIASES.update({module: module for module in MODULES.values()})
ALIASES.update(
    {
        "ti2v": "ltx_pipelines.ti2vid_two_stages",
        "ti2v_hq": "ltx_pipelines.ti2vid_two_stages_hq",
        "one_stage": "ltx_pipelines.ti2vid_one_stage",
        "keyframes": "ltx_pipelines.keyframe_interpolation",
        "a2v": "ltx_pipelines.a2vid_two_stage",
        "hdr": "ltx_pipelines.hdr_ic_lora",
        "t2a": "ltx_pipelines.t2a_one_stage",
        "dfr": "ltx_pipelines.dfr_pipeline",
    }
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "List or inspect help for known LTX-2 ltx_pipelines CLI modules. "
            "Only '--help' can be executed; generation arguments are never accepted."
        )
    )
    parser.add_argument(
        "module",
        nargs="?",
        help="Module alias or full module name. Omit with --list to show available modules.",
    )
    parser.add_argument("--list", action="store_true", help="List known modules and aliases, then exit.")
    parser.add_argument("--json", action="store_true", help="Emit module data as JSON for --list or --print-command.")
    parser.add_argument(
        "--print-command",
        action="store_true",
        help="Print the safe help command instead of running it. This is the default when a module is provided.",
    )
    parser.add_argument(
        "--run-help",
        action="store_true",
        help="Execute the safe '<python> -m <module> --help' command and stream its output.",
    )
    parser.add_argument(
        "--python",
        default="python",
        help="Python executable to use for --run-help or command printing (default: python on PATH).",
    )
    return parser


def resolve_module(name: str) -> str:
    try:
        return ALIASES[name]
    except KeyError as exc:
        choices = ", ".join(MODULES)
        raise SystemExit(f"Unknown module alias {name!r}. Known primary aliases: {choices}") from exc


def command_for(python: str, module: str) -> list[str]:
    return [python, "-m", module, "--help"]


def list_modules(as_json: bool) -> None:
    data = {
        "modules": [{"alias": alias, "module": module} for alias, module in MODULES.items()],
        "extra_aliases": {key: value for key, value in sorted(ALIASES.items()) if key not in MODULES and key != value},
    }
    if as_json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return
    print("Known LTX-2 pipeline CLI modules:")
    for item in data["modules"]:
        print(f"  {item['alias']:<24} {item['module']}")
    print("\nUseful aliases:")
    for alias, module in data["extra_aliases"].items():
        print(f"  {alias:<24} {module}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list or not args.module:
        if args.module and args.list:
            parser.error("--list does not take a module argument")
        list_modules(args.json)
        return 0

    module = resolve_module(args.module)
    cmd = command_for(args.python, module)

    if args.run_help and args.print_command:
        parser.error("Choose only one of --run-help or --print-command")

    if args.run_help:
        return subprocess.run(cmd, check=False).returncode

    if args.json:
        print(json.dumps({"module": module, "command": cmd}, indent=2))
    else:
        print(shlex.join(cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
