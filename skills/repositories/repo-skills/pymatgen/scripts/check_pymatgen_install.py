#!/usr/bin/env python3
"""Redacted pymatgen installation and console-script check.

Example:
    python scripts/check_pymatgen_install.py
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

MODULES = [
    "pymatgen",
    "pymatgen.core",
    "pymatgen.analysis.local_env",
    "pymatgen.entries.compatibility",
    "pymatgen.ext.matproj",
    "pymatgen.analysis.diffraction.xrd",
]
CONSOLE_SCRIPTS = ["pmg", "get_environment", "feff_plot_cross_section", "feff_plot_dos"]


def distribution_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_status(module: str) -> dict[str, object]:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"module": module, "ok": True, "has_file": bool(getattr(imported, "__file__", None))}


def find_script(script: str) -> str | None:
    path = shutil.which(script)
    if path:
        return path

    script_dir = Path(sys.executable).resolve().parent
    candidate = script_dir / script
    if candidate.exists():
        return str(candidate)

    windows_candidate = script_dir / f"{script}.exe"
    if windows_candidate.exists():
        return str(windows_candidate)
    return None


def script_status(script: str, run_help: bool) -> dict[str, object]:
    path = find_script(script)
    result: dict[str, object] = {"script": script, "found": path is not None}
    if path and run_help:
        try:
            completed = subprocess.run(
                [path, "--help"],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
            )
        except Exception as exc:  # pragma: no cover - diagnostic path
            result.update({"help_ok": False, "error": f"{type(exc).__name__}: {exc}"})
        else:
            result.update(
                {
                    "help_ok": completed.returncode == 0,
                    "returncode": completed.returncode,
                    "stdout_first_line": (completed.stdout.strip().splitlines() or [""])[0],
                    "stderr_first_line": (completed.stderr.strip().splitlines() or [""])[0],
                }
            )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check pymatgen imports and console scripts without leaking local paths.")
    parser.add_argument("--run-help", action="store_true", help="Run safe --help checks for discovered console scripts.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args(argv)

    report = {
        "python_version": sys.version.split()[0],
        "distributions": {
            "pymatgen": distribution_version("pymatgen"),
            "pymatgen-core": distribution_version("pymatgen-core"),
        },
        "imports": [import_status(module) for module in MODULES],
        "console_scripts": [script_status(script, args.run_help) for script in CONSOLE_SCRIPTS],
    }
    ok = all(item["ok"] for item in report["imports"]) and report["distributions"]["pymatgen"] is not None

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"pymatgen distribution: {report['distributions']['pymatgen'] or 'missing'}")
        print(f"pymatgen-core distribution: {report['distributions']['pymatgen-core'] or 'missing'}")
        for item in report["imports"]:
            status = "ok" if item["ok"] else item.get("error", "failed")
            print(f"import {item['module']}: {status}")
        for item in report["console_scripts"]:
            suffix = "found" if item["found"] else "missing"
            if "help_ok" in item:
                suffix += f", help_ok={item['help_ok']}"
            print(f"script {item['script']}: {suffix}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
