#!/usr/bin/env python3
"""Safely inspect InvokeAI operations CLI help without starting the server.

This helper never runs InvokeAI server startup or mutating user-management
operations. It prefers installed console scripts when available and falls back
to bundled help facts distilled from InvokeAI 6.13.0.post1 source evidence.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import shutil
import subprocess
import sys
from textwrap import dedent

COMMANDS = {
    "invokeai-web": {
        "entry_point": "invokeai.app.run_app:run_app",
        "summary": "Start the InvokeAI FastAPI/React web server.",
        "safe": True,
        "fallback_help": dedent(
            """
            usage: invokeai-web [--root ROOT] [--config CONFIG_FILE] [--version] [-h]

            Invoke Studio

            options:
              --root ROOT           Path to the runtime root directory. If omitted, the app searches: INVOKEAI_ROOT,
                                    active virtualenv parent, then ~/invokeai.
              --config CONFIG_FILE  Path to invokeai.yaml. If omitted, the app searches in the root directory.
              --version             Displays the version and exits.
              -h, --help            Show this help message and exit.
            """
        ).strip(),
    },
    "invoke-useradd": {
        "entry_point": "invokeai.app.util.user_management:useradd",
        "summary": "Add a user to the configured InvokeAI database.",
        "mutates": True,
        "fallback_help": dedent(
            """
            usage: invoke-useradd [--root ROOT] [--email EMAIL] [--password PASSWORD] [--name NAME] [--admin] [-h]

            Add a user to the InvokeAI database. If no email/password are provided, runs interactively.
            Options: --root/-r, --email/-e, --password/-p, --name/-n, --admin/-a.
            """
        ).strip(),
    },
    "invoke-userdel": {
        "entry_point": "invokeai.app.util.user_management:userdel",
        "summary": "Delete a user from the configured InvokeAI database.",
        "mutates": True,
        "fallback_help": dedent(
            """
            usage: invoke-userdel [--root ROOT] [--email EMAIL] [--force] [-h]

            Delete a user from the InvokeAI database. Without --force, prompts for confirmation.
            Options: --root/-r, --email/-e, --force/-f.
            """
        ).strip(),
    },
    "invoke-userlist": {
        "entry_point": "invokeai.app.util.user_management:userlist",
        "summary": "List users from the configured InvokeAI database.",
        "mutates": False,
        "fallback_help": dedent(
            """
            usage: invoke-userlist [--root ROOT] [--json] [-h]

            List users from the InvokeAI database.
            Options: --root/-r, --json.
            """
        ).strip(),
    },
    "invoke-usermod": {
        "entry_point": "invokeai.app.util.user_management:usermod",
        "summary": "Modify a user in the configured InvokeAI database.",
        "mutates": True,
        "fallback_help": dedent(
            """
            usage: invoke-usermod [--root ROOT] [--email EMAIL] [--name NAME] [--password PASSWORD]
                                  [--admin | --no-admin] [-h]

            Modify a user in the InvokeAI database. Without --email, runs interactively.
            Options: --root/-r, --email/-e, --name/-n, --password/-p, --admin/-a, --no-admin.
            """
        ).strip(),
    },
}

ALIASES = {
    "web": ["invokeai-web"],
    "users": ["invoke-useradd", "invoke-userdel", "invoke-userlist", "invoke-usermod"],
    "all": list(COMMANDS),
}


def resolve_commands(selection: str) -> list[str]:
    if selection in COMMANDS:
        return [selection]
    return ALIASES[selection]


def installed_entry_points() -> dict[str, str]:
    try:
        eps = metadata.entry_points()
        scripts = eps.select(group="console_scripts") if hasattr(eps, "select") else eps.get("console_scripts", [])
        return {ep.name: ep.value for ep in scripts if ep.name in COMMANDS}
    except Exception:
        return {}


def run_help(command: str, timeout: float) -> tuple[bool, str]:
    executable = shutil.which(command)
    if executable is None:
        return False, f"{command!r} is not on PATH."
    try:
        result = subprocess.run(
            [executable, "--help"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, f"Timed out while running {command} --help."
    except OSError as exc:
        return False, f"Failed to run {command} --help: {exc}"

    output = (result.stdout or result.stderr).strip()
    if result.returncode != 0:
        return False, f"{command} --help exited with {result.returncode}. Output:\n{output}"
    return True, output


def print_command(command: str, use_installed: bool, timeout: float, entry_points: dict[str, str]) -> int:
    info = COMMANDS[command]
    print(f"## {command}")
    print(f"Summary: {info['summary']}")
    print(f"Expected entry point: {info['entry_point']}")
    if command in entry_points:
        print(f"Installed entry point: {entry_points[command]}")
    else:
        print("Installed entry point: not found in current Python environment")
    if info.get("mutates"):
        print("Safety: mutates the configured users database unless only --help is requested.")
    else:
        print("Safety: help inspection is read-only; command behavior may still read configured runtime state.")

    if use_installed:
        ok, output = run_help(command, timeout)
        if ok:
            print("\nInstalled --help output:\n")
            print(output)
            print()
            return 0
        print(f"\nInstalled help unavailable: {output}")
        print("Bundled fallback help:\n")
    else:
        print("\nBundled fallback help:\n")
    print(info["fallback_help"])
    print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect InvokeAI operations CLI help safely.")
    parser.add_argument(
        "--command",
        choices=sorted(list(COMMANDS) + list(ALIASES)),
        default="all",
        help="Command or command group to inspect.",
    )
    parser.add_argument(
        "--installed",
        action="store_true",
        help="Run installed '<command> --help' when the executable is on PATH. Never runs mutating command modes.",
    )
    parser.add_argument("--timeout", type=float, default=5.0, help="Seconds to wait for each installed --help call.")
    args = parser.parse_args()

    entry_points = installed_entry_points()
    for command in resolve_commands(args.command):
        print_command(command, args.installed, args.timeout, entry_points)
    return 0


if __name__ == "__main__":
    sys.exit(main())
