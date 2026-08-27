#!/usr/bin/env python3
"""Read-only OmicVerse package health check for generated repo-skill users."""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from typing import Any


def version_of(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def import_status(module: str) -> dict[str, Any]:
    try:
        mod = importlib.import_module(module)
        return {"ok": True, "file": getattr(mod, "__file__", None), "all_count": len(getattr(mod, "__all__", []) or [])}
    except Exception as exc:  # diagnostics script
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def run_help(exe: str) -> dict[str, Any]:
    path = shutil.which(exe)
    if not path:
        return {"ok": False, "found": False, "error": "not on PATH"}
    try:
        proc = subprocess.run([path, "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return {"ok": proc.returncode == 0, "found": True, "returncode": proc.returncode, "stdout_head": proc.stdout.splitlines()[:8], "stderr_head": proc.stderr.splitlines()[:8]}
    except Exception as exc:  # diagnostics script
        return {"ok": False, "found": True, "error_type": type(exc).__name__, "error": str(exc)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect an OmicVerse installation without downloading data or starting services.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--include-cli", action="store_true", help="Run safe --help checks for console scripts.")
    parser.add_argument("--modules", default="omicverse,omicverse.pp,omicverse.single,omicverse.bulk,omicverse.space,omicverse.es,omicverse.metabol,omicverse.protein,omicverse.micro,omicverse.airr,omicverse.genetics,omicverse.alignment,omicverse.mcp", help="Comma-separated modules to import-check.")
    args = parser.parse_args(argv)

    modules = [module.strip() for module in args.modules.split(",") if module.strip()]
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "distributions": {name: version_of(name) for name in ["omicverse", "numpy", "pandas", "anndata", "scanpy", "scipy", "matplotlib"]},
        "imports": {module: import_status(module) for module in modules},
    }
    try:
        import omicverse as ov
        report["root"] = {
            "version": getattr(ov, "__version__", None),
            "lazy_modules": sorted(list(getattr(ov, "_LAZY_MODULES", []))),
            "lazy_attrs": sorted(list(getattr(ov, "_LAZY_ATTRS", {}).keys())),
        }
    except Exception as exc:
        report["root"] = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}

    if args.include_cli:
        report["cli"] = {exe: run_help(exe) for exe in ["omicverse", "omicverse-mcp", "ov-skill-seeker"]}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print("Distributions:")
        for name, version in report["distributions"].items():
            print(f"  {name}: {version or 'missing'}")
        print("Imports:")
        for module, status in report["imports"].items():
            print(f"  {module}: {'ok' if status['ok'] else 'FAIL ' + status.get('error_type', '')}")
        if args.include_cli:
            print("CLI:")
            for exe, status in report["cli"].items():
                print(f"  {exe}: {'ok' if status.get('ok') else 'FAIL'}")

    import_failures = [module for module, status in report["imports"].items() if not status.get("ok")]
    return 1 if import_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
