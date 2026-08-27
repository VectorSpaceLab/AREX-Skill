#!/usr/bin/env python3
"""Run read-only SMARTS package, API, and CLI diagnostics.

Works from any current directory. It does not install packages, build
scenarios, start services, or run a simulation. Use it to distinguish the core
CPU installation from optional integrations.

Example: ``python scripts/check_smarts_install.py --json``
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version


def _import(name: str) -> dict[str, str]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # diagnostic output should be concise
        return {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
    return {"status": "ok", "location": str(getattr(module, "__file__", ""))}


def _cli_help() -> dict[str, object]:
    executable = shutil.which("scl")
    if executable is None:
        sibling = "scl.exe" if sys.platform == "win32" else "scl"
        candidate = __import__("pathlib").Path(sys.executable).with_name(sibling)
        executable = str(candidate) if candidate.is_file() else None
    if executable is None:
        return {
            "status": "failed",
            "error": "scl executable is not on PATH and was not found beside this Python",
        }
    try:
        completed = subprocess.run(
            [executable, "--help"],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
    return {
        "status": "ok" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "commands_seen": [
            line.strip().split()[0]
            for line in completed.stdout.splitlines()
            if line.startswith("  ") and line.strip() and not line.strip().startswith("-")
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnose an installed SMARTS package without side effects.")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a summary")
    args = parser.parse_args(argv)

    try:
        distribution = version("smarts")
    except PackageNotFoundError:
        distribution = "not-installed"

    core_modules = [
        "smarts",
        "smarts.core",
        "smarts.env",
        "smarts.env.gymnasium.hiway_env_v1",
        "smarts.sstudio",
        "cli.cli",
        "envision",
    ]
    optional_modules = [
        "gymnasium",
        "panda3d.core",
        "opendrive2lanelet",
        "ray",
        "ray.rllib",
        "torch",
        "tensorflow",
        "traci",
        "sumolib",
        "rospkg",
        "av2",
        "visdom",
    ]
    report = {
        "python": sys.version.split()[0],
        "distribution": distribution,
        "core_imports": {name: _import(name) for name in core_modules},
        "optional_modules": {
            name: {"available": bool(importlib.util.find_spec(name))}
            if "." not in name or importlib.util.find_spec(name.rsplit(".", 1)[0])
            else {"available": False, "error": "parent module unavailable"}
            for name in optional_modules
        },
        "scl_help": _cli_help(),
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"SMARTS distribution: {distribution}")
        for name, result in report["core_imports"].items():
            print(f"{name}: {result['status']}")
        print(f"scl --help: {report['scl_help']['status']}")
        print("Optional modules:")
        for name, result in report["optional_modules"].items():
            print(f"  {name}: {'available' if result['available'] else 'missing'}")

    core_ok = distribution != "not-installed" and all(
        result["status"] == "ok" for result in report["core_imports"].values()
    )
    return 0 if core_ok and report["scl_help"]["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
