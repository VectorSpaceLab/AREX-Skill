#!/usr/bin/env python3
"""Safely verify DataChain CLI help or skill-list output.

This helper never runs a mutating DataChain command. For command help it appends
``--help`` to an allow-listed command path. For ``--skill-list`` it imports the
public skill-list function when possible, or runs ``datachain skill list`` in an
isolated temporary DataChain/HOME directory when subprocess mode is selected.

Examples:
  python cli_help_smoke.py
  python cli_help_smoke.py job run
  python cli_help_smoke.py dataset ls --via subprocess
  python cli_help_smoke.py --skill-list
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

HELP_PATHS = {
    (),
    ("auth",),
    ("auth", "login"),
    ("auth", "logout"),
    ("auth", "team"),
    ("auth", "token"),
    ("bucket",),
    ("bucket", "status"),
    ("clear-cache",),
    ("clone",),
    ("completion",),
    ("cp",),
    ("dataset",),
    ("dataset", "edit"),
    ("dataset", "ls"),
    ("dataset", "pull"),
    ("dataset", "remove"),
    ("dataset", "rm"),
    ("ds",),
    ("ds", "edit"),
    ("ds", "ls"),
    ("ds", "pull"),
    ("ds", "remove"),
    ("ds", "rm"),
    ("du",),
    ("find",),
    ("gc",),
    ("index",),
    ("job",),
    ("job", "cancel"),
    ("job", "clusters"),
    ("job", "logs"),
    ("job", "ls"),
    ("job", "run"),
    ("ls",),
    ("pipeline",),
    ("pipeline", "create"),
    ("pipeline", "list"),
    ("pipeline", "pause"),
    ("pipeline", "remove-job"),
    ("pipeline", "resume"),
    ("pipeline", "status"),
    ("show",),
    ("skill",),
    ("skill", "install"),
    ("skill", "list"),
    ("skill", "uninstall"),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify DataChain CLI help or skill-list output without running "
            "mutating commands or requiring Studio credentials."
        )
    )
    parser.add_argument(
        "command",
        nargs="*",
        metavar="CMD",
        help=(
            "Allow-listed command path to inspect, e.g. `ls`, `job run`, "
            "or `dataset ls`. Omit for top-level help. The helper appends --help."
        ),
    )
    parser.add_argument(
        "--skill-list",
        action="store_true",
        help="Verify `datachain skill list` output instead of command help.",
    )
    parser.add_argument(
        "--via",
        choices=("auto", "import", "subprocess"),
        default="auto",
        help="Use parser/function import, subprocess execution, or auto fallback.",
    )
    parser.add_argument(
        "--datachain-bin",
        default="datachain",
        help="Executable name/path for subprocess mode (default: datachain).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress captured help/list output; still prints a final OK line.",
    )
    return parser


def _validate_help_path(tokens: Sequence[str]) -> tuple[str, ...]:
    path = tuple(tokens)
    if any(token == "--help" or token.startswith("-") for token in path):
        raise SystemExit("error: provide only command/subcommand names; --help is added automatically")
    if path not in HELP_PATHS:
        allowed = ", ".join(" ".join(p) or "<top-level>" for p in sorted(HELP_PATHS))
        raise SystemExit(f"error: unsupported command path {path!r}. Allowed: {allowed}")
    return path


def _assert_help_output(output: str, command_path: Sequence[str]) -> None:
    expected = "datachain" if not command_path else "datachain " + " ".join(command_path)
    lowered = output.lower()
    if "usage:" not in lowered or expected not in output:
        raise AssertionError(
            f"help output did not contain expected usage for {expected!r}:\n{output[:500]}"
        )


def _assert_skill_list_output(output: str) -> None:
    for required in ("Skill", "Targets", "core", "knowledge", "jobs"):
        if required not in output:
            raise AssertionError(f"skill list output missing {required!r}:\n{output[:500]}")


def _print_if_needed(output: str, quiet: bool) -> None:
    if not quiet:
        print(output, end="" if output.endswith("\n") else "\n")


def run_help_via_import(command_path: Sequence[str]) -> str:
    from datachain.cli.parser import get_parser

    parser = get_parser()
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        try:
            parser.parse_args([*command_path, "--help"])
        except SystemExit as exc:
            if exc.code not in (0, None):
                raise
    output = stdout.getvalue()
    _assert_help_output(output, command_path)
    return output


def run_skill_list_via_import() -> str:
    from datachain.cli.commands.skill import list_skills

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        result = list_skills()
    if result not in (0, None):
        raise AssertionError(f"list_skills returned {result!r}")
    output = stdout.getvalue()
    _assert_skill_list_output(output)
    return output


def _isolated_env(tmpdir: str) -> dict[str, str]:
    env = dict(os.environ)
    env.pop("DATACHAIN_STUDIO_TOKEN", None)
    env.pop("DATACHAIN_STUDIO_TEAM", None)
    env["HOME"] = str(Path(tmpdir) / "home")
    env["DATACHAIN_ROOT_DIR"] = str(Path(tmpdir) / "root")
    env["DATACHAIN_GLOBAL_CONFIG_DIR"] = str(Path(tmpdir) / "global-config")
    env["DATACHAIN_SYSTEM_CONFIG_DIR"] = str(Path(tmpdir) / "system-config")
    env["DATACHAIN_NO_ANALYTICS"] = "1"
    return env


def run_subprocess(args: list[str], datachain_bin: str) -> str:
    exe = shutil.which(datachain_bin) if os.sep not in datachain_bin else datachain_bin
    if not exe:
        raise FileNotFoundError(f"could not find DataChain executable {datachain_bin!r}")
    with tempfile.TemporaryDirectory(prefix="datachain-cli-help-") as tmpdir:
        env = _isolated_env(tmpdir)
        completed = subprocess.run(  # noqa: S603 - executable is explicit/allow-listed by user option.
            [exe, *args],
            cwd=tmpdir,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    output = completed.stdout + completed.stderr
    if completed.returncode != 0:
        raise RuntimeError(
            f"subprocess returned {completed.returncode} for {[datachain_bin, *args]!r}:\n{output}"
        )
    return output


def run_help_via_subprocess(command_path: Sequence[str], datachain_bin: str) -> str:
    output = run_subprocess([*command_path, "--help"], datachain_bin)
    _assert_help_output(output, command_path)
    return output


def run_skill_list_via_subprocess(datachain_bin: str) -> str:
    output = run_subprocess(["skill", "list"], datachain_bin)
    _assert_skill_list_output(output)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command_path = _validate_help_path(args.command)

    attempts: list[tuple[str, Exception]] = []
    modes = [args.via] if args.via != "auto" else ["import", "subprocess"]
    for mode in modes:
        try:
            if args.skill_list:
                output = (
                    run_skill_list_via_import()
                    if mode == "import"
                    else run_skill_list_via_subprocess(args.datachain_bin)
                )
                _print_if_needed(output, args.quiet)
                print(f"OK: verified datachain skill list via {mode}")
            else:
                output = (
                    run_help_via_import(command_path)
                    if mode == "import"
                    else run_help_via_subprocess(command_path, args.datachain_bin)
                )
                label = "datachain" if not command_path else "datachain " + " ".join(command_path)
                _print_if_needed(output, args.quiet)
                print(f"OK: verified {label} --help via {mode}")
            return 0
        except Exception as exc:  # pragma: no cover - depends on local install mode.
            attempts.append((mode, exc))
            if args.via != "auto":
                break

    for mode, exc in attempts:
        print(f"{mode} failed: {exc}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
