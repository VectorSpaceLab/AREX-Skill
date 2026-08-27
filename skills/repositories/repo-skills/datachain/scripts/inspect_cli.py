#!/usr/bin/env python3
"""Safely inspect DataChain CLI help output.

The script appends --help to an allow-listed command path and captures parser
output without running the command action. It is safe for commands that would be
mutating if executed normally.

Examples:
  python inspect_cli.py
  python inspect_cli.py job run
  python inspect_cli.py dataset ls --json
"""

import argparse
import contextlib
import io
import json
from collections.abc import Sequence

HELP_PATHS = {
    (),
    ("auth",), ("auth", "login"), ("auth", "logout"), ("auth", "team"), ("auth", "token"),
    ("bucket",), ("bucket", "status"),
    ("clear-cache",), ("clone",), ("completion",), ("cp",),
    ("dataset",), ("dataset", "edit"), ("dataset", "ls"), ("dataset", "pull"),
    ("dataset", "remove"), ("dataset", "rm"),
    ("ds",), ("ds", "edit"), ("ds", "ls"), ("ds", "pull"), ("ds", "remove"), ("ds", "rm"),
    ("du",), ("find",), ("gc",), ("index",),
    ("job",), ("job", "cancel"), ("job", "clusters"), ("job", "logs"), ("job", "ls"), ("job", "run"),
    ("ls",),
    ("pipeline",), ("pipeline", "create"), ("pipeline", "list"), ("pipeline", "pause"),
    ("pipeline", "remove-job"), ("pipeline", "resume"), ("pipeline", "status"),
    ("show",),
    ("skill",), ("skill", "install"), ("skill", "list"), ("skill", "uninstall"),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only DataChain CLI help inspector.")
    parser.add_argument("command", nargs="*", help="Command path such as `job run` or `dataset ls`.")
    parser.add_argument("--json", action="store_true", help="Emit JSON with command path and help text.")
    return parser


def validate_path(tokens: Sequence[str]) -> tuple[str, ...]:
    path = tuple(tokens)
    if any(token.startswith("-") for token in path):
        raise SystemExit("provide only command names; --help is appended automatically")
    if path not in HELP_PATHS:
        allowed = ", ".join(" ".join(p) or "<top-level>" for p in sorted(HELP_PATHS))
        raise SystemExit(f"unsupported DataChain command path {path!r}. Allowed: {allowed}")
    return path


def get_help(command_path: Sequence[str]) -> str:
    try:
        from datachain.cli.parser import get_parser
    except Exception as exc:  # pragma: no cover - environment dependent
        raise SystemExit(f"could not import DataChain CLI parser: {exc}") from exc
    parser = get_parser()
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        try:
            parser.parse_args([*command_path, "--help"])
        except SystemExit as exc:
            if exc.code not in (0, None):
                raise
    text = output.getvalue()
    expected = "datachain" if not command_path else "datachain " + " ".join(command_path)
    if "usage:" not in text.lower() or expected not in text:
        raise AssertionError(f"help output did not look like {expected!r} help")
    return text


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = validate_path(args.command)
    text = get_help(path)
    if args.json:
        print(json.dumps({"command": ["datachain", *path, "--help"], "help": text}, indent=2))
    else:
        print(text, end="" if text.endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
