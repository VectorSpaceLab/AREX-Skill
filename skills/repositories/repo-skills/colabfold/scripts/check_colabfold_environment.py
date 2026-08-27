#!/usr/bin/env python3
"""Read-only ColabFold environment diagnostic.

Examples:
  python scripts/check_colabfold_environment.py --check-entry-points
  python scripts/check_colabfold_environment.py --check-entry-points --check-mmseqs --json
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


def check_import(module: str) -> dict[str, Any]:
    try:
        imported = importlib.import_module(module)
        return {"module": module, "ok": True, "file": getattr(imported, "__file__", None)}
    except Exception as exc:  # noqa: BLE001 - diagnostic script should capture import failures
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def check_entry_point(command: str) -> dict[str, Any]:
    path = shutil.which(command)
    result: dict[str, Any] = {"command": command, "path": path, "ok": False}
    if not path:
        result["error"] = "not found on PATH"
        return result
    try:
        completed = subprocess.run([path, "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        result.update({"ok": completed.returncode == 0, "returncode": completed.returncode})
        text = (completed.stdout or completed.stderr).splitlines()
        result["first_line"] = text[0] if text else ""
        if completed.returncode != 0:
            result["error"] = (completed.stderr or completed.stdout).strip().splitlines()[:4]
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ColabFold package, optional dependencies, entry points, and local tools without running prediction.")
    parser.add_argument("--check-entry-points", action="store_true", help="Run --help for ColabFold console scripts found on PATH.")
    parser.add_argument("--check-mmseqs", action="store_true", help="Check whether the mmseqs executable is available on PATH.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of a text summary.")
    args = parser.parse_args()

    report: dict[str, Any] = {"python": sys.version.split()[0]}
    try:
        report["distribution"] = {"name": "colabfold", "version": metadata.version("colabfold"), "ok": True}
    except Exception as exc:  # noqa: BLE001
        report["distribution"] = {"name": "colabfold", "ok": False, "error": f"{type(exc).__name__}: {exc}"}

    modules = ["colabfold", "colabfold.input", "colabfold.mmseqs.search", "alphafold", "jax", "openmm", "pdbfixer"]
    report["imports"] = [check_import(module) for module in modules]

    if args.check_entry_points:
        commands = ["colabfold_batch", "colabfold_search", "colabfold_split_msas", "colabfold_relax"]
        report["entry_points"] = [check_entry_point(command) for command in commands]

    if args.check_mmseqs:
        mmseqs = shutil.which("mmseqs")
        report["mmseqs"] = {"ok": bool(mmseqs), "path": mmseqs}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        dist = report["distribution"]
        print(f"colabfold distribution: {'ok ' + dist.get('version', '') if dist.get('ok') else 'missing - ' + dist.get('error', '')}")
        for item in report["imports"]:
            status = "ok" if item["ok"] else f"missing ({item['error']})"
            print(f"import {item['module']}: {status}")
        for item in report.get("entry_points", []):
            status = "ok" if item["ok"] else f"not ready ({item.get('error')})"
            print(f"{item['command']}: {status}")
        if "mmseqs" in report:
            print(f"mmseqs: {'ok ' + report['mmseqs']['path'] if report['mmseqs']['ok'] else 'missing'}")

    required_ok = report["distribution"].get("ok") and any(item["module"] == "colabfold" and item["ok"] for item in report["imports"])
    return 0 if required_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
