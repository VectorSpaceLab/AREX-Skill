#!/usr/bin/env python3
"""Safely inspect a local CrewAI installation without running crews, tools, LLMs, or hosted commands.

Examples:
  python scripts/check_crewai_environment.py
  python scripts/check_crewai_environment.py --json
"""

from __future__ import annotations

import argparse
import importlib
from importlib import metadata
import json
import shutil
import subprocess
import sys
from typing import Any


DISTRIBUTIONS = [
    ("crewai", "crewai"),
    ("crewai-cli", "crewai_cli"),
    ("crewai-tools", "crewai_tools"),
    ("crewai-files", "crewai_files"),
    ("crewai-core", "crewai_core"),
    ("crewai-devtools", "crewai_devtools"),
]


def distribution_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic script reports broad import failures.
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "version": getattr(module, "__version__", None)}


def cli_commands() -> dict[str, Any]:
    try:
        from crewai_cli.cli import crewai
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "commands": sorted(crewai.commands.keys())}


def pip_check(timeout: int) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--skip-pip-check", action="store_true", help="Skip python -m pip check.")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout seconds for pip check.")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "crewai_executable": shutil.which("crewai"),
        "distributions": {},
        "imports": {},
        "cli": cli_commands(),
    }
    for distribution, module in DISTRIBUTIONS:
        report["distributions"][distribution] = distribution_version(distribution)
        report["imports"][module] = import_status(module)
    if not args.skip_pip_check:
        report["pip_check"] = pip_check(args.timeout)

    ok = all(item.get("ok") for item in report["imports"].values()) and report["cli"].get("ok", False)
    if "pip_check" in report:
        ok = ok and report["pip_check"].get("ok", False)
    report["ok"] = ok

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print(f"crewai executable: {report['crewai_executable'] or 'not found on PATH'}")
        print("\nDistributions:")
        for name, version in report["distributions"].items():
            print(f"  {name}: {version or 'not installed'}")
        print("\nImports:")
        for module, status in report["imports"].items():
            if status["ok"]:
                print(f"  OK {module} {status.get('version') or ''}".rstrip())
            else:
                print(f"  FAIL {module}: {status['error']}")
        if report["cli"].get("ok"):
            print("\nCLI commands: " + ", ".join(report["cli"]["commands"]))
        else:
            print(f"\nCLI import failed: {report['cli']['error']}")
        if "pip_check" in report:
            status = report["pip_check"]
            print("\npip check: " + ("OK" if status["ok"] else "FAILED"))
            output = status["stdout"] or status["stderr"]
            if output:
                print(output)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
