#!/usr/bin/env python3
"""Run safe labelme installation, CLI, and optional-surface checks.

This diagnostic does not start the GUI, download AI models, or mutate a Config
File. Run it with the same Python environment that should execute labelme:
``python check_labelme_environment.py``.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
from typing import Any


BASE_IMPORTS = [
    "labelme",
    "labelme._label_file",
    "labelme._shape",
    "labelme._config",
]
OPTIONAL_IMPORTS = {
    "osam": "AI model session support",
    "onnxruntime": "CPU model runtime",
    "lxml": "VOC bounding-box export",
    "pycocotools": "COCO export",
    "pytestqt": "Qt test support",
}


def _run_module_help() -> dict[str, Any]:
    command = [sys.executable, "-m", "labelme", "--help"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    return {
        "command": " ".join(command),
        "returncode": result.returncode,
        "usage_seen": result.returncode == 0 and result.stdout.startswith("usage:"),
        "stderr": result.stderr.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--require-display",
        action="store_true",
        help="fail if no DISPLAY/WAYLAND_DISPLAY is visible",
    )
    args = parser.parse_args()

    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "distribution": None,
        "imports": {},
        "optional_imports": {},
        "cli": {},
        "display": {
            "DISPLAY": os.environ.get("DISPLAY"),
            "WAYLAND_DISPLAY": os.environ.get("WAYLAND_DISPLAY"),
        },
        "warnings": [],
    }
    try:
        report["distribution"] = importlib.metadata.version("labelme")
    except importlib.metadata.PackageNotFoundError:
        report["warnings"].append("labelme distribution metadata is not installed")

    failed = False
    for module_name in BASE_IMPORTS:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # keep diagnostics useful for Qt/ABI failures
            report["imports"][module_name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            failed = True
        else:
            report["imports"][module_name] = {"ok": True}

    for module_name, purpose in OPTIONAL_IMPORTS.items():
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            report["optional_imports"][module_name] = {
                "ok": False,
                "purpose": purpose,
                "error": f"{type(exc).__name__}: {exc}",
            }
        else:
            report["optional_imports"][module_name] = {"ok": True, "purpose": purpose}

    try:
        report["cli"] = _run_module_help()
        if not report["cli"]["usage_seen"]:
            failed = True
    except Exception as exc:
        report["cli"] = {"returncode": None, "error": f"{type(exc).__name__}: {exc}"}
        failed = True

    if args.require_display and not (
        report["display"]["DISPLAY"] or report["display"]["WAYLAND_DISPLAY"]
    ):
        report["warnings"].append("no display variable is set; use Xvfb or a desktop session for GUI tests")
        failed = True
    elif not (report["display"]["DISPLAY"] or report["display"]["WAYLAND_DISPLAY"]):
        report["warnings"].append("no display variable is set; CLI/data workflows remain usable")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"labelme distribution: {report['distribution'] or 'missing'}")
        print(f"Python: {report['python']} ({report['python_executable']})")
        print("Base imports:", ", ".join(name for name, value in report["imports"].items() if value["ok"]))
        missing = [name for name, value in report["optional_imports"].items() if not value["ok"]]
        if missing:
            print("Optional imports unavailable:", ", ".join(missing))
        print("CLI help:", "PASS" if report["cli"].get("usage_seen") else "FAIL")
        if report["warnings"]:
            print("Warnings:")
            for warning in report["warnings"]:
                print(f"- {warning}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
