#!/usr/bin/env python3
"""Check AnyLabeling translation/resource tool availability without mutation.

The repository's resource scripts use PyQt6 tools for UI/translation extraction
and PySide6-Essentials tools for Qt6 resource compilation and .qm generation.
This helper only probes executable availability and optionally checks that a
generated resources.py file imports PyQt6 rather than PySide6.

Examples:
  python check_language_tools.py
  python check_language_tools.py --resource-py anylabeling/resources/resources.py
  python check_language_tools.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_TOOLS = ("pyuic6", "pylupdate6", "pyside6-lrelease", "pyside6-rcc")


def which_near_python(cmd: str) -> str | None:
    candidate = Path(sys.executable).resolve().parent / cmd
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return str(candidate)
    return shutil.which(cmd)


def probe_version(path: str) -> dict[str, Any]:
    for flag in ("--version", "-version", "-v"):
        try:
            proc = subprocess.run(
                [path, flag],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False,
            )
        except Exception as exc:  # noqa: BLE001 - diagnostic helper
            return {"ok": False, "error": str(exc)}
        output = (proc.stdout or proc.stderr).strip().splitlines()
        if proc.returncode == 0 and output:
            return {"ok": True, "flag": flag, "version": output[0][:200]}
    return {"ok": True, "flag": None, "version": "found; version flag not recognized"}


def check_resource_import(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing", "path": str(path)}
    text = path.read_text(encoding="utf-8", errors="replace")[:10000]
    has_pyqt = "from PyQt6 import" in text or "import PyQt6" in text
    has_pyside = "from PySide6 import" in text or "import PySide6" in text
    if has_pyqt and not has_pyside:
        status = "pyqt6"
    elif has_pyside:
        status = "pyside6-imports-present"
    else:
        status = "no-qt-import-detected"
    return {"status": status, "path": str(path), "has_pyqt6": has_pyqt, "has_pyside6": has_pyside}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    tools = []
    for cmd in args.tools:
        path = which_near_python(cmd)
        if path is None:
            tools.append({"name": cmd, "found": False, "path": None, "version": None})
        else:
            tools.append({"name": cmd, "found": True, "path": path, "version": probe_version(path)})
    missing = [tool["name"] for tool in tools if not tool["found"]]
    report: dict[str, Any] = {
        "python": sys.executable,
        "tools": tools,
        "missing": missing,
        "ok": not missing,
    }
    if args.resource_py:
        report["resource_py"] = check_resource_import(Path(args.resource_py).expanduser())
        if report["resource_py"]["status"] == "pyside6-imports-present":
            report["ok"] = False
    return report


def print_text(report: dict[str, Any]) -> None:
    print("AnyLabeling language/resource tool check")
    for tool in report["tools"]:
        if tool["found"]:
            version = tool["version"] or {}
            print(f"OK {tool['name']}: {tool['path']} ({version.get('version', 'found')})")
        else:
            print(f"MISSING {tool['name']}")
    if "resource_py" in report:
        res = report["resource_py"]
        print(f"resources.py: {res['status']} ({res['path']})")
    if report["missing"]:
        print("Missing tools usually come from PyQt6 and PySide6-Essentials developer dependencies.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tools", nargs="*", default=list(DEFAULT_TOOLS), help="tool commands to probe")
    parser.add_argument("--resource-py", help="optional generated resources.py to inspect for PyQt6/PySide6 imports")
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    args = parser.parse_args(argv)
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
