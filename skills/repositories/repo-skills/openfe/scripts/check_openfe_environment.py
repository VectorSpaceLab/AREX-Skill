#!/usr/bin/env python3
"""Read-only OpenFE environment diagnostic.

This helper imports OpenFE-related packages, checks the `openfe --help` CLI,
and reports OpenMM platforms when available. It never runs simulations,
downloads data, submits jobs, uploads information, or mutates files.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def import_check(name: str) -> dict[str, Any]:
    item: dict[str, Any] = {"module": name, "ok": False}
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostics should report broad failures.
        item["error"] = f"{type(exc).__name__}: {exc}"
        return item
    item["ok"] = True
    item["version"] = getattr(module, "__version__", None)
    return item


def resolve_executable(executable: str) -> str | None:
    resolved = shutil.which(executable)
    if resolved:
        return resolved
    candidate = Path(executable)
    if candidate.is_file():
        return str(candidate)
    sibling = Path(sys.executable).with_name(executable)
    if sibling.is_file():
        return str(sibling)
    return None


def cli_help(executable: str, timeout: int) -> dict[str, Any]:
    resolved = resolve_executable(executable)
    result: dict[str, Any] = {"executable": executable, "found": bool(resolved), "ok": False}
    if not resolved:
        result["error"] = "executable not found on PATH or next to the active Python"
        return result
    try:
        proc = subprocess.run(
            [resolved, "--help"],
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result
    result.update(
        {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout_first_lines": proc.stdout.splitlines()[:25],
            "stderr_first_lines": proc.stderr.splitlines()[:25],
        }
    )
    return result


def openmm_platforms() -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False, "platforms": []}
    try:
        import openmm
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result
    try:
        count = openmm.Platform.getNumPlatforms()
        result["platforms"] = [openmm.Platform.getPlatform(i).getName() for i in range(count)]
        result["ok"] = True
        result["openmm_version"] = getattr(openmm, "version", None).version if hasattr(openmm, "version") else None
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only OpenFE environment diagnostics.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a readable summary.")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout seconds for CLI help checks.")
    parser.add_argument("--openfe-executable", default="openfe", help="OpenFE CLI executable name or path.")
    args = parser.parse_args()

    modules = [
        "openfe",
        "openfecli",
        "gufe",
        "openmm",
        "openff.toolkit",
        "rdkit",
        "lomap",
        "kartograf",
        "konnektor",
        "perses",
        "cinnabar",
    ]
    report = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "pymbar_disable_jax": os.environ.get("PYMBAR_DISABLE_JAX"),
        "imports": [import_check(name) for name in modules],
        "cli": cli_help(args.openfe_executable, args.timeout),
        "openmm_platforms": openmm_platforms(),
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print(f"Platform: {report['platform']}")
        print(f"PYMBAR_DISABLE_JAX: {report['pymbar_disable_jax']}")
        print("\nImports:")
        for item in report["imports"]:
            status = "ok" if item["ok"] else "missing/error"
            extra = f" ({item.get('version')})" if item.get("version") else ""
            print(f"- {item['module']}: {status}{extra}")
            if item.get("error"):
                print(f"  {item['error']}")
        print("\nCLI:")
        print(f"- {args.openfe_executable}: {'ok' if report['cli']['ok'] else 'missing/error'}")
        if report["cli"].get("stderr_first_lines"):
            print("  stderr:", " | ".join(report["cli"]["stderr_first_lines"][:3]))
        print("\nOpenMM platforms:")
        if report["openmm_platforms"]["ok"]:
            print("- " + ", ".join(report["openmm_platforms"]["platforms"]))
        else:
            print(f"- unavailable: {report['openmm_platforms'].get('error')}")

    hard_failures = [item for item in report["imports"] if item["module"] in {"openfe", "openfecli"} and not item["ok"]]
    return 1 if hard_failures or not report["cli"]["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
