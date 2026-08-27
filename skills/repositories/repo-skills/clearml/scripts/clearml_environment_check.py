#!/usr/bin/env python3
"""Read-only ClearML environment signal checker.

The checker imports optional modules only to verify availability, runs no ClearML
server calls, starts no agents/services, and never prints secret values.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

SECRET_ENV = ("CLEARML_API_ACCESS_KEY", "CLEARML_API_SECRET_KEY")
CONFIG_ENV = ("CLEARML_API_HOST", "CLEARML_WEB_HOST", "CLEARML_FILES_HOST")
CLI_COMMANDS = ("clearml-init", "clearml-debug", "clearml-task", "clearml-data", "clearml-param-search")
OPTIONAL_MODULES = {
    "router": ("fastapi", "uvicorn", "httpx"),
    "s3": ("boto3",),
    "gs": ("google.cloud.storage",),
    "azure": ("azure.storage.blob",),
}


def has_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def run_cli_help(command: str, timeout: float) -> Dict[str, Any]:
    exe = shutil.which(command)
    if not exe:
        return {"available": False, "returncode": None, "signal": "not-on-path"}
    try:
        proc = subprocess.run(
            [exe, "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"available": True, "returncode": None, "signal": "help-timeout"}
    return {
        "available": True,
        "returncode": proc.returncode,
        "signal": "help-ok" if proc.returncode == 0 else "help-nonzero",
    }


def check(timeout: float, include_help: bool) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "clearml": {"importable": False, "version": None},
        "credentials": {
            "secret_env_present": {key: bool(os.environ.get(key)) for key in SECRET_ENV},
            "host_env_present": {key: bool(os.environ.get(key)) for key in CONFIG_ENV},
            "config_file_signals": [],
        },
        "optional_modules": {},
        "cli": {},
    }

    try:
        import clearml  # type: ignore

        report["clearml"] = {"importable": True, "version": getattr(clearml, "__version__", None)}
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["clearml"] = {"importable": False, "error_type": type(exc).__name__}

    for path in (Path.home() / "clearml.conf", Path.home() / ".clearml.conf"):
        if path.exists():
            report["credentials"]["config_file_signals"].append(str(path.name))

    for extra, modules in OPTIONAL_MODULES.items():
        report["optional_modules"][extra] = {module: has_module(module) for module in modules}

    for command in CLI_COMMANDS:
        exe = shutil.which(command)
        report["cli"][command] = {"on_path": bool(exe)}
        if include_help:
            report["cli"][command].update(run_cli_help(command, timeout=timeout))

    return report


def print_text(report: Dict[str, Any]) -> None:
    print(f"Python: {report['python']}")
    clearml = report["clearml"]
    print(f"ClearML importable: {clearml.get('importable')} version={clearml.get('version')}")
    print("Credential signals:")
    for key, present in report["credentials"]["host_env_present"].items():
        print(f"  {key}: {'present' if present else 'missing'}")
    for key, present in report["credentials"]["secret_env_present"].items():
        print(f"  {key}: {'present' if present else 'missing'}")
    if report["credentials"]["config_file_signals"]:
        print("  config file signal: present")
    else:
        print("  config file signal: missing")
    print("Optional modules:")
    for extra, modules in report["optional_modules"].items():
        status = ", ".join(f"{name}={'ok' if value else 'missing'}" for name, value in modules.items())
        print(f"  {extra}: {status}")
    print("CLI commands:")
    for command, info in report["cli"].items():
        signal = info.get("signal", "not-checked")
        print(f"  {command}: {'on PATH' if info.get('on_path') else 'missing'} ({signal})")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only ClearML environment signal checker")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--check-help", action="store_true", help="Run each ClearML CLI with --help")
    parser.add_argument("--timeout", type=float, default=10.0, help="Timeout per CLI help check")
    args = parser.parse_args(argv)

    report = check(timeout=args.timeout, include_help=args.check_help)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["clearml"].get("importable") else 1


if __name__ == "__main__":
    raise SystemExit(main())
