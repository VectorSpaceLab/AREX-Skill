#!/usr/bin/env python3
"""Safely inspect the installed PaperQA `pqa` CLI help parser.

The script only runs `pqa --help` and subcommand help. It does not call
`pqa ask`, `pqa index`, embeddings, LLMs, or metadata providers. By default it
sets PQA_HOME to a temporary directory for the inspected subprocesses.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

COMMANDS = ("view", "save", "ask", "search", "index")
IMPORTANT_GLOBAL_FLAGS = (
    "--settings",
    "--index",
    "--llm",
    "--summary_llm",
    "--embedding",
    "--temperature",
    "--verbosity",
    "--agent.index.paper_directory",
    "--agent.index.index_directory",
    "--agent.index.manifest_file",
    "--agent.index.name",
    "--agent.index.recurse_subdirectories",
    "--agent.index.sync_with_paper_directory",
    "--agent.index.use_absolute_paper_directory",
    "--agent.rebuild_index",
)


@dataclass
class HelpResult:
    command: list[str]
    ok: bool
    returncode: int
    stdout: str
    stderr: str


@dataclass
class Inspection:
    executable_found: bool
    executable_name: str | None
    global_help_ok: bool
    commands_detected: list[str]
    important_flags_detected: list[str]
    help_results: list[HelpResult]
    warnings: list[str]


def _run_help(executable: str, extra_args: Iterable[str], env: dict[str, str]) -> HelpResult:
    cmd = [executable, *extra_args, "--help"]
    proc = subprocess.run(  # noqa: S603 - executable is resolved by shutil.which
        cmd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=30,
    )
    return HelpResult(
        command=[Path(cmd[0]).name, *cmd[1:]],
        ok=proc.returncode == 0,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def inspect_cli(use_temp_home: bool = True) -> Inspection:
    executable = shutil.which("pqa")
    if not executable:
        sibling = Path(sys.executable).with_name("pqa")
        executable = str(sibling) if sibling.exists() else None
    if not executable:
        return Inspection(
            executable_found=False,
            executable_name=None,
            global_help_ok=False,
            commands_detected=[],
            important_flags_detected=[],
            help_results=[],
            warnings=["No `pqa` executable was found on PATH or beside sys.executable."],
        )

    warnings: list[str] = []
    env = os.environ.copy()
    tempdir_obj: tempfile.TemporaryDirectory[str] | None = None
    if use_temp_home:
        tempdir_obj = tempfile.TemporaryDirectory(prefix="pqa-help-")
        env["PQA_HOME"] = tempdir_obj.name

    try:
        results = [_run_help(executable, [], env)]
        for command in COMMANDS:
            results.append(_run_help(executable, [command], env))
    finally:
        if tempdir_obj is not None:
            tempdir_obj.cleanup()

    global_text = results[0].stdout + "\n" + results[0].stderr
    commands_detected = [cmd for cmd in COMMANDS if re.search(rf"\b{cmd}\b", global_text)]
    important_flags_detected = [flag for flag in IMPORTANT_GLOBAL_FLAGS if flag in global_text]

    for result in results:
        if not result.ok:
            warnings.append(
                "Help command failed: "
                + " ".join(result.command)
                + f" (exit {result.returncode})"
            )
    missing_commands = sorted(set(COMMANDS) - set(commands_detected))
    if missing_commands:
        warnings.append("Global help did not advertise commands: " + ", ".join(missing_commands))
    missing_flags = sorted(set(IMPORTANT_GLOBAL_FLAGS) - set(important_flags_detected))
    if missing_flags:
        warnings.append("Global help did not advertise important flags: " + ", ".join(missing_flags))

    return Inspection(
        executable_found=True,
        executable_name=Path(executable).name,
        global_help_ok=results[0].ok,
        commands_detected=commands_detected,
        important_flags_detected=important_flags_detected,
        help_results=results,
        warnings=warnings,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely inspect PaperQA pqa help output.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    parser.add_argument(
        "--keep-pqa-home",
        action="store_true",
        help="Do not replace PQA_HOME with a temporary directory for help subprocesses.",
    )
    parser.add_argument(
        "--show-help-text",
        action="store_true",
        help="Include captured help text in text output. JSON output always includes it.",
    )
    args = parser.parse_args()

    inspection = inspect_cli(use_temp_home=not args.keep_pqa_home)

    if args.json:
        payload = asdict(inspection)
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("PaperQA CLI inspection")
        print(f"executable_found: {inspection.executable_found}")
        if inspection.executable_name:
            print(f"executable_name: {inspection.executable_name}")
        print(f"global_help_ok: {inspection.global_help_ok}")
        print("commands_detected: " + ", ".join(inspection.commands_detected))
        print("important_flags_detected: " + ", ".join(inspection.important_flags_detected))
        if inspection.warnings:
            print("warnings:")
            for warning in inspection.warnings:
                print(f"  - {warning}")
        if args.show_help_text:
            for result in inspection.help_results:
                print("\n$ " + " ".join(result.command))
                print(result.stdout.rstrip())
                if result.stderr:
                    print("stderr:")
                    print(result.stderr.rstrip())

    return 0 if inspection.executable_found and inspection.global_help_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
