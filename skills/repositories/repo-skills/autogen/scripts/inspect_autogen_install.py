#!/usr/bin/env python3
"""Inspect installed AutoGen packages without side effects."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

PACKAGES = {
    "autogen-core": "autogen_core",
    "autogen-agentchat": "autogen_agentchat",
    "autogen-ext": "autogen_ext",
    "pyautogen": "pyautogen",
    "agbench": "agbench",
    "autogenstudio": "autogenstudio",
    "magentic-one-cli": "magentic_one_cli",
}

COMMANDS = ["agbench", "autogenstudio", "m1"]


def command_path(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    candidate = Path(sys.executable).resolve().parent / name
    if candidate.exists():
        return str(candidate)
    if sys.platform.startswith("win"):
        candidate = Path(sys.executable).resolve().parent / f"{name}.exe"
        if candidate.exists():
            return str(candidate)
    return None


def check_distribution(dist_name: str, import_name: str) -> dict[str, Any]:
    item: dict[str, Any] = {"distribution": dist_name, "import": import_name}
    try:
        dist = metadata.distribution(dist_name)
        item.update(
            installed=True,
            version=dist.version,
            requires_python=dist.metadata.get("Requires-Python"),
            entry_points=[
                {"group": ep.group, "name": ep.name, "value": ep.value}
                for ep in dist.entry_points
                if ep.group == "console_scripts"
            ],
        )
    except metadata.PackageNotFoundError:
        item["installed"] = False

    try:
        module = importlib.import_module(import_name)
        item["import_ok"] = True
        item["module_version"] = getattr(module, "__version__", None)
    except Exception as exc:
        item["import_ok"] = False
        item["import_error"] = f"{type(exc).__name__}: {exc}"
    return item


def check_command(name: str, timeout: float) -> dict[str, Any]:
    resolved = command_path(name)
    if not resolved:
        return {"command": name, "available": False, "error": "not found"}
    try:
        completed = subprocess.run(
            [resolved, "--help"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return {"command": name, "available": True, "error": f"timeout after {exc.timeout}s"}
    return {
        "command": name,
        "available": True,
        "returncode": completed.returncode,
        "stdout_preview": completed.stdout.strip()[:800],
        "stderr_preview": completed.stderr.strip()[:800],
    }


def collect(timeout: float) -> dict[str, Any]:
    packages = [check_distribution(dist, module) for dist, module in PACKAGES.items()]
    versions = {item["distribution"]: item.get("version") for item in packages if item.get("installed")}
    findings: list[str] = []
    modern = any((versions.get(name) or "").startswith("0.7") for name in ("autogen-core", "autogen-agentchat", "autogen-ext"))
    if modern and versions.get("autogenstudio"):
        findings.append("autogenstudio may target older AutoGen ranges; verify dependency compatibility before use.")
    if modern and versions.get("magentic-one-cli"):
        findings.append("magentic-one-cli may target older AutoGen ranges; verify dependency compatibility before use.")
    if versions.get("pyautogen"):
        findings.append("Current pyautogen is a compatibility/proxy package; legacy v0.2 code may need old pins or migration.")
    return {
        "python": sys.version.split()[0],
        "safety": {
            "imports_only": True,
            "runs_help_only": True,
            "starts_servers": False,
            "runs_benchmarks": False,
            "calls_model_providers": False,
            "uses_docker": False,
        },
        "packages": packages,
        "commands": [check_command(name, timeout) for name in COMMANDS],
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect installed AutoGen packages safely.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--timeout", type=float, default=8.0, help="Per-command help timeout.")
    args = parser.parse_args()
    report = collect(args.timeout)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        for item in report["packages"]:
            status = f"{item.get('version')} import_ok={item.get('import_ok')}" if item.get("installed") else "not installed"
            print(f"- {item['distribution']}: {status}")
        if report["findings"]:
            print("Findings:")
            for finding in report["findings"]:
                print(f"- {finding}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
