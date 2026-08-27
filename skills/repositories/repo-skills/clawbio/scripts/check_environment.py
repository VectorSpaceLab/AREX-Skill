#!/usr/bin/env python3
"""Run read-only ClawBio package and CLI environment checks.

This helper intentionally does not run a scientific demo, contact a service,
start MCP/bots, create profiles, or write output artifacts. It checks the
public distribution, stable imports/signatures, CLI help, and optional module
availability. Run it from any directory after installing ClawBio.

Example:
    python check_environment.py
    python check_environment.py --json
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import inspect
import json
import shutil
import subprocess
import sys
from typing import Any


def _check_import(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {"name": name, "status": "available", "file": getattr(module, "__file__", None)}
    except Exception as exc:  # diagnostic output should name optional failures
        return {"name": name, "status": "unavailable", "error": f"{type(exc).__name__}: {exc}"}


def run() -> dict[str, Any]:
    result: dict[str, Any] = {
        "python": {"version": sys.version.split()[0], "executable": sys.executable},
        "distribution": {},
        "imports": [],
        "cli": {},
        "api": {},
        "optional": [],
    }
    try:
        result["distribution"] = {"name": "clawbio", "version": importlib.metadata.version("clawbio")}
    except importlib.metadata.PackageNotFoundError as exc:
        result["distribution"] = {"name": "clawbio", "status": "missing", "error": str(exc)}
        return result

    for name in ("clawbio", "clawbio.cli", "clawbio.common.profile", "clawbio.skill_intents"):
        result["imports"].append(_check_import(name))

    cli = shutil.which("clawbio")
    result["cli"]["executable"] = cli
    if cli:
        proc = subprocess.run([cli, "--help"], capture_output=True, text=True, timeout=30)
        result["cli"].update({"status": "pass" if proc.returncode == 0 else "fail", "exit_code": proc.returncode, "help_contains_run": "run" in proc.stdout})
    else:
        result["cli"]["status"] = "missing"

    try:
        from clawbio import list_skills, run_skill, upload_profile
        result["api"] = {
            "status": "pass",
            "list_skills": str(inspect.signature(list_skills)),
            "run_skill": str(inspect.signature(run_skill)),
            "upload_profile": str(inspect.signature(upload_profile)),
        }
    except Exception as exc:
        result["api"] = {"status": "fail", "error": f"{type(exc).__name__}: {exc}"}

    for name in ("mcp", "telegram", "discord", "nextflow"):
        if name == "nextflow":
            result["optional"].append({"name": name, "status": "available" if shutil.which(name) else "unavailable"})
        else:
            result["optional"].append(_check_import(name))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only ClawBio package and CLI diagnostics")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"clawbio {result.get('distribution', {}).get('version', 'missing')}")
        print(f"CLI: {result.get('cli', {}).get('status', 'unknown')}")
        print(f"API: {result.get('api', {}).get('status', 'unknown')}")
        for item in result["imports"] + result["optional"]:
            print(f"{item['name']}: {item['status']}")
    required_ok = result.get("distribution", {}).get("version") and result.get("api", {}).get("status") == "pass"
    return 0 if required_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
