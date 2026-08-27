#!/usr/bin/env python3
"""Safe AutoGen tooling inspection.

This script reports installed distribution metadata and help text availability for
AutoGen developer tools. It intentionally avoids starting servers, running
benchmarks, launching Docker, invoking model providers, or executing Magentic-One
tasks.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DISTRIBUTIONS = [
    "autogen-core",
    "autogen-agentchat",
    "autogen-ext",
    "pyautogen",
    "agbench",
    "autogenstudio",
    "magentic-one-cli",
]

COMMANDS = {
    "agbench": [["agbench", "--help"]],
    "autogenstudio": [["autogenstudio", "--help"]],
    "m1": [["m1", "--help"], ["m1", "--sample-config"]],
}

AUTO_GEN_DEPENDENCY_NAMES = ("autogen", "pyautogen")


@dataclass
class CommandCheck:
    command: list[str]
    available: bool
    returncode: int | None = None
    stdout_preview: str = ""
    stderr_preview: str = ""
    error: str | None = None


def preview(text: str, limit: int = 1200) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def distribution_report(name: str) -> dict[str, Any]:
    try:
        dist = metadata.distribution(name)
    except metadata.PackageNotFoundError:
        return {"name": name, "installed": False}

    requirements = list(dist.requires or [])
    autogen_requirements = [
        req for req in requirements if any(token in req.lower() for token in AUTO_GEN_DEPENDENCY_NAMES)
    ]
    return {
        "name": name,
        "installed": True,
        "version": dist.version,
        "requires_python": dist.metadata.get("Requires-Python"),
        "autogen_requirements": autogen_requirements,
        "entry_points": [
            {"group": ep.group, "name": ep.name, "value": ep.value}
            for ep in dist.entry_points
            if ep.group == "console_scripts"
        ],
    }


def resolve_executable(executable: str) -> str | None:
    resolved = shutil.which(executable)
    if resolved is not None:
        return resolved

    scripts_dir = Path(sys.executable).resolve().parent
    candidate = scripts_dir / executable
    if os.name == "nt":
        windows_candidate = scripts_dir / f"{executable}.exe"
        if windows_candidate.exists():
            return str(windows_candidate)
    if candidate.exists():
        return str(candidate)
    return None


def run_command_check(command: list[str], timeout: float) -> CommandCheck:
    resolved = resolve_executable(command[0])
    if resolved is None:
        return CommandCheck(command=command, available=False, error="executable not found on PATH or beside current Python")

    display_command = list(command)
    run_command = [resolved, *command[1:]]
    try:
        completed = subprocess.run(
            run_command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandCheck(command=command, available=True, error=f"timed out after {exc.timeout} seconds")
    except OSError as exc:
        return CommandCheck(command=command, available=True, error=str(exc))

    return CommandCheck(
        command=display_command,
        available=True,
        returncode=completed.returncode,
        stdout_preview=preview(completed.stdout),
        stderr_preview=preview(completed.stderr),
    )


def compatibility_findings(distributions: list[dict[str, Any]]) -> list[str]:
    versions = {item["name"]: item.get("version") for item in distributions if item.get("installed")}
    findings: list[str] = []

    modern_autogen = any(
        (versions.get(name) or "").startswith("0.7")
        for name in ("autogen-core", "autogen-agentchat", "autogen-ext")
    )
    if modern_autogen and versions.get("magentic-one-cli"):
        findings.append(
            "magentic-one-cli metadata in this repo targets AutoGen >=0.4.4,<0.5; verify before mixing with 0.7.x packages."
        )
    if modern_autogen and versions.get("autogenstudio"):
        findings.append(
            "autogenstudio metadata in this repo targets AutoGen <0.7; verify before mixing with 0.7.x packages."
        )
    if versions.get("pyautogen"):
        findings.append("Current pyautogen is a proxy package for autogen-agentchat, not the legacy 0.2 API unless pinned.")
    if not versions.get("agbench"):
        findings.append("agbench is not installed; only static package planning is possible.")

    return findings


def collect(timeout: float) -> dict[str, Any]:
    distributions = [distribution_report(name) for name in DISTRIBUTIONS]
    commands: dict[str, list[dict[str, Any]]] = {}
    for label, checks in COMMANDS.items():
        commands[label] = [run_command_check(command, timeout).__dict__ for command in checks]

    return {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "safety": {
            "starts_servers": False,
            "runs_benchmarks": False,
            "uses_docker": False,
            "calls_model_providers": False,
            "uses_network_intentionally": False,
        },
        "distributions": distributions,
        "commands": commands,
        "compatibility_findings": compatibility_findings(distributions),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely inspect AutoGen tooling package metadata and CLI help.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--timeout", type=float, default=8.0, help="Per-command timeout for help checks.")
    args = parser.parse_args()

    report = collect(timeout=args.timeout)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print("Safety: help/metadata only; no servers, benchmarks, Docker, providers, or intentional network calls")
        print("\nDistributions:")
        for item in report["distributions"]:
            if item["installed"]:
                print(f"- {item['name']} {item['version']} (Python {item.get('requires_python') or 'unspecified'})")
                for req in item.get("autogen_requirements", []):
                    print(f"  requires: {req}")
            else:
                print(f"- {item['name']} not installed")
        print("\nCommands:")
        for label, checks in report["commands"].items():
            for check in checks:
                command_text = " ".join(check["command"])
                status = "available" if check["available"] else "missing"
                suffix = f", rc={check['returncode']}" if check.get("returncode") is not None else ""
                print(f"- {command_text}: {status}{suffix}")
                if check.get("error"):
                    print(f"  error: {check['error']}")
        if report["compatibility_findings"]:
            print("\nCompatibility findings:")
            for finding in report["compatibility_findings"]:
                print(f"- {finding}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
