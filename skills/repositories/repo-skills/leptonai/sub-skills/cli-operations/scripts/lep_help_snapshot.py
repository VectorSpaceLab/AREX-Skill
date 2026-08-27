#!/usr/bin/env python3
"""Safe command-tree snapshot for the installed LeptonAI `lep` CLI.

This script runs only help/version commands:

    lep --version
    lep --help
    lep <group> --help

It strips common Lepton credential environment variables from subprocesses,
uses a timeout, and parses command names from click help output. It does not run
workspace reads or live cloud operations.
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
from dataclasses import dataclass, asdict
from typing import Iterable, List, Optional

DEFAULT_GROUPS = [
    "endpoint",
    "deployment",
    "workspace",
    "job",
    "pod",
    "secret",
    "storage",
    "file",
    "ingress",
    "log",
    "raycluster",
    "template",
    "finetune",
    "node",
]

STRIP_ENV_PREFIXES = ("LEP_",)
STRIP_ENV_NAMES = {
    "LEPTON_WORKSPACE_ID",
    "LEPTON_WORKSPACE_TOKEN",
    "LEPTON_WORKSPACE_URL",
    "LEPTON_WORKSPACE_ORIGIN_URL",
    "LEPTON_API_TOKEN",
    "LEPTON_API_URL",
}

COMMAND_RE = re.compile(r"^\s{2}([A-Za-z0-9][A-Za-z0-9_-]*)\s{2,}.*$")


@dataclass
class CommandResult:
    args: List[str]
    exit_code: Optional[int]
    timed_out: bool
    output: str


@dataclass
class GroupSnapshot:
    group: str
    ok: bool
    exit_code: Optional[int]
    timed_out: bool
    commands: List[str]
    output_excerpt: str


def parse_groups(values: Optional[List[str]]) -> List[str]:
    if not values:
        return list(DEFAULT_GROUPS)
    groups: List[str] = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if part:
                groups.append(part)
    return groups or list(DEFAULT_GROUPS)


def safe_env(temp_cache: str) -> dict:
    env = {}
    for key, value in os.environ.items():
        if key in STRIP_ENV_NAMES:
            continue
        if any(key.startswith(prefix) for prefix in STRIP_ENV_PREFIXES):
            continue
        env[key] = value
    env["NO_COLOR"] = "1"
    env["TERM"] = "dumb"
    env["PYTHONUNBUFFERED"] = "1"
    env["LEPTON_CACHE_DIR"] = temp_cache
    return env


def run_help(
    lep_exec: str,
    lep_display: str,
    extra_args: Iterable[str],
    timeout: float,
    env: dict,
) -> CommandResult:
    run_args = [lep_exec, *extra_args]
    display_args = [lep_display, *extra_args]
    try:
        completed = subprocess.run(
            run_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
        return CommandResult(args=display_args, exit_code=completed.returncode, timed_out=False, output=completed.stdout)
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        return CommandResult(args=display_args, exit_code=None, timed_out=True, output=output + "\n[TIMED OUT]")
    except OSError as exc:
        detail = getattr(exc, "strerror", None) or exc.__class__.__name__
        return CommandResult(args=display_args, exit_code=127, timed_out=False, output=f"ERROR: unable to execute lep command: {detail}\n")


def parse_command_names(help_output: str) -> List[str]:
    commands: List[str] = []
    in_commands = False
    for line in help_output.splitlines():
        if line.strip() == "Commands:":
            in_commands = True
            continue
        if in_commands and line and not line.startswith(" "):
            break
        if not in_commands:
            continue
        match = COMMAND_RE.match(line)
        if match:
            commands.append(match.group(1))
    return commands


def excerpt(text: str, limit: int = 1200) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n..."


def print_text(snapshot: dict) -> None:
    print(f"lep executable: {snapshot['lepExecutable']}")
    version = snapshot.get("version", {})
    print(f"version exit={version.get('exit_code')} timeout={version.get('timed_out')}")
    if version.get("output"):
        print(f"version: {version['output'].strip()}")
    print("top-level commands:")
    top_commands = snapshot.get("topCommands") or []
    print("  " + (", ".join(top_commands) if top_commands else "<none parsed>"))
    print("groups:")
    for group in snapshot.get("groups", []):
        status = "ok" if group["ok"] else f"failed exit={group['exit_code']}"
        if group["timed_out"]:
            status = "timed out"
        command_text = ", ".join(group["commands"]) if group["commands"] else "<none parsed>"
        print(f"  {group['group']}: {status}; commands: {command_text}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Snapshot installed `lep` help safely.")
    parser.add_argument("--lep", default="lep", help="CLI executable name or path; default: lep")
    parser.add_argument(
        "--groups",
        nargs="*",
        default=None,
        help="Groups to inspect, as space-separated or comma-separated names. Default includes visible groups and known hidden aliases.",
    )
    parser.add_argument("--timeout", type=float, default=10.0, help="Timeout in seconds per help command.")
    parser.add_argument("--json", action="store_true", help="Print a JSON snapshot instead of text.")
    args = parser.parse_args(argv)

    using_plain_name = os.path.basename(args.lep) == args.lep
    lep_path = shutil.which(args.lep) if using_plain_name else args.lep
    lep_display = args.lep if using_plain_name else "<custom>"
    if not lep_path:
        message = "`lep` was not found on PATH. Install or expose the LeptonAI CLI, then rerun this help-only snapshot."
        if args.json:
            print(json.dumps({"ok": False, "error": message}, indent=2))
        else:
            print(f"ERROR: {message}", file=sys.stderr)
        return 127

    groups = parse_groups(args.groups)
    with tempfile.TemporaryDirectory(prefix="lep-help-cache-") as cache_dir:
        env = safe_env(cache_dir)
        version = run_help(lep_path, lep_display, ["--version"], args.timeout, env)
        top = run_help(lep_path, lep_display, ["--help"], args.timeout, env)
        group_snapshots: List[GroupSnapshot] = []
        for group in groups:
            result = run_help(lep_path, lep_display, [group, "--help"], args.timeout, env)
            group_snapshots.append(
                GroupSnapshot(
                    group=group,
                    ok=(result.exit_code == 0 and not result.timed_out),
                    exit_code=result.exit_code,
                    timed_out=result.timed_out,
                    commands=parse_command_names(result.output),
                    output_excerpt=excerpt(result.output),
                )
            )

    snapshot = {
        "ok": top.exit_code == 0 and not top.timed_out,
        "lepExecutable": lep_display,
        "version": asdict(version),
        "topHelp": {
            "exit_code": top.exit_code,
            "timed_out": top.timed_out,
            "output_excerpt": excerpt(top.output),
        },
        "topCommands": parse_command_names(top.output),
        "groups": [asdict(item) for item in group_snapshots],
    }

    if args.json:
        print(json.dumps(snapshot, indent=2, sort_keys=True))
    else:
        print_text(snapshot)
    return 0 if snapshot["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
