#!/usr/bin/env python3
"""Check a REINVENT4 installation without running molecular design jobs."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify REINVENT4 import, distribution metadata, and safe CLI help commands."
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON report.")
    parser.add_argument(
        "--skip-cli",
        action="store_true",
        help="Skip console-script --help checks and only verify imports/metadata.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds for each CLI help command.",
    )
    return parser.parse_args()


def check_import(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return {"name": name, "ok": False, "error": repr(exc)}
    return {"name": name, "ok": True, "module": getattr(module, "__name__", name)}


def check_distribution(name: str) -> dict[str, Any]:
    try:
        version = metadata.version(name)
    except Exception as exc:
        return {"name": name, "ok": False, "error": repr(exc)}
    return {"name": name, "ok": True, "version": version}


def check_cli(command: str, timeout: int) -> dict[str, Any]:
    sibling = Path(sys.executable).with_name(command)
    executable = str(sibling) if sibling.exists() else shutil.which(command)
    if executable is None:
        return {"command": command, "ok": False, "error": "not found beside current Python or on PATH"}
    try:
        result = subprocess.run(
            [executable, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:
        return {"command": command, "ok": False, "error": repr(exc)}
    return {
        "command": command,
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout_first_line": (result.stdout.splitlines() or [""])[0],
        "stderr_first_line": (result.stderr.splitlines() or [""])[0],
    }


def main() -> int:
    args = parse_args()
    report: dict[str, Any] = {
        "distribution": check_distribution("reinvent"),
        "imports": [check_import("reinvent"), check_import("reinvent_plugins")],
        "cli": [],
    }
    if not args.skip_cli:
        report["cli"] = [
            check_cli("reinvent", args.timeout),
            check_cli("reinvent_datapre", args.timeout),
        ]

    ok = bool(report["distribution"].get("ok"))
    ok = ok and all(item.get("ok") for item in report["imports"])
    ok = ok and all(item.get("ok") for item in report["cli"])

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"distribution reinvent: {'OK' if report['distribution'].get('ok') else 'FAIL'}")
        if report["distribution"].get("version"):
            print(f"version: {report['distribution']['version']}")
        for item in report["imports"]:
            print(f"import {item['name']}: {'OK' if item.get('ok') else 'FAIL'}")
            if item.get("error"):
                print(f"  {item['error']}")
        for item in report["cli"]:
            print(f"{item['command']} --help: {'OK' if item.get('ok') else 'FAIL'}")
            if item.get("error"):
                print(f"  {item['error']}")
            elif item.get("stderr_first_line"):
                print(f"  stderr: {item['stderr_first_line']}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
