#!/usr/bin/env python3
"""Safe OpenCompass environment check.

This script checks package metadata, importability, CLI help, and selected optional
modules without running model inference, downloading datasets, or using credentials.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from typing import Any


def check_import(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {
            "name": name,
            "ok": True,
            "version": getattr(module, "__version__", None),
            "file": getattr(module, "__file__", None),
        }
    except Exception as exc:  # noqa: BLE001 - report diagnostic, do not crash.
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def run_cli_help(command: str, timeout: int) -> dict[str, Any]:
    executable = shutil.which(command)
    if not executable:
        return {"command": command, "ok": False, "error": "not found on PATH"}
    try:
        proc = subprocess.run(
            [executable, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"command": command, "ok": False, "error": f"timed out after {timeout}s"}
    return {
        "command": command,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_head": proc.stdout.splitlines()[:20],
        "stderr_head": proc.stderr.splitlines()[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check an OpenCompass runtime without running evaluations.")
    parser.add_argument("--cli", default="opencompass", help="CLI command name to check; default: opencompass")
    parser.add_argument("--timeout", type=int, default=20, help="CLI help timeout in seconds")
    parser.add_argument(
        "--optional-module",
        action="append",
        default=[],
        help="Additional optional module to import-check, e.g. vllm or lmdeploy",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "distribution": {},
        "imports": [],
        "cli_help": {},
    }

    try:
        report["distribution"] = {"name": "opencompass", "ok": True, "version": metadata.version("opencompass")}
    except metadata.PackageNotFoundError:
        report["distribution"] = {"name": "opencompass", "ok": False, "error": "distribution metadata not found"}

    modules = ["opencompass", "mmengine", "torch", "transformers", "datasets"] + args.optional_module
    report["imports"] = [check_import(name) for name in modules]
    report["cli_help"] = run_cli_help(args.cli, args.timeout)

    ok = bool(report["distribution"].get("ok")) and any(
        item["name"] == "opencompass" and item.get("ok") for item in report["imports"]
    ) and bool(report["cli_help"].get("ok"))

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        dist = report["distribution"]
        print(f"Distribution opencompass: {'ok ' + dist.get('version', '') if dist.get('ok') else 'missing'}")
        for item in report["imports"]:
            suffix = f" {item.get('version')}" if item.get("version") else ""
            print(f"Import {item['name']}: {'ok' + suffix if item.get('ok') else item.get('error')}")
        cli = report["cli_help"]
        print(f"CLI {args.cli} --help: {'ok' if cli.get('ok') else cli.get('error', 'failed')}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
