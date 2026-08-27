#!/usr/bin/env python3
"""Safely inspect the installed Evaluate CLI without network or Hub mutation."""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import shutil
import subprocess
import sys
from typing import Any


def check_import(module_name: str) -> dict[str, Any]:
    try:
        importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - report exact import failure for troubleshooting.
        return {
            "ok": False,
            "module": module_name,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    return {"ok": True, "module": module_name}


def check_cli_help() -> dict[str, Any]:
    executable = shutil.which("evaluate-cli")
    if executable is not None:
        result = subprocess.run(
            [executable, "--help"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return {
            "ok": result.returncode == 0,
            "method": "entrypoint",
            "executable_found": True,
            "returncode": result.returncode,
            "stdout_first_line": result.stdout.splitlines()[0] if result.stdout.splitlines() else "",
            "stderr": result.stderr.strip(),
        }

    try:
        cli_module = importlib.import_module("evaluate.commands.evaluate_cli")
    except Exception as exc:  # noqa: BLE001 - report exact import failure for troubleshooting.
        return {
            "ok": False,
            "method": "module-import",
            "executable_found": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    saved_argv = sys.argv[:]
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    try:
        sys.argv = ["evaluate-cli", "--help"]
        with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(captured_stderr):
            try:
                cli_module.main()
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 1
            else:
                code = 0
    finally:
        sys.argv = saved_argv

    stdout = captured_stdout.getvalue()
    stderr = captured_stderr.getvalue()
    return {
        "ok": code == 0,
        "method": "module-main",
        "executable_found": False,
        "returncode": code,
        "stdout_first_line": stdout.splitlines()[0] if stdout.splitlines() else "",
        "stderr": stderr.strip(),
    }


def build_report() -> dict[str, Any]:
    return {
        "imports": [
            check_import("evaluate"),
            check_import("cookiecutter.main"),
            check_import("huggingface_hub"),
            check_import("evaluate.commands.evaluate_cli"),
        ],
        "cli_help": check_cli_help(),
        "safety": "No create, clone, login, push, or Hub metadata update commands are executed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print the full machine-readable inspection report.")
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["cli_help"]["ok"] else 1

    print("Evaluate CLI safe inspection")
    print("Safety: no create, clone, login, push, or Hub metadata update commands are executed.")
    print("")
    for item in report["imports"]:
        if item["ok"]:
            print(f"[ok] import {item['module']}")
        else:
            print(f"[fail] import {item['module']}: {item['error_type']}: {item['error']}")
    cli_help = report["cli_help"]
    if cli_help["ok"]:
        print(f"[ok] evaluate-cli --help via {cli_help['method']}: {cli_help['stdout_first_line']}")
    else:
        detail = cli_help.get("error") or cli_help.get("stderr") or "unknown failure"
        error_type = cli_help.get("error_type", "CLIHelpError")
        print(f"[fail] evaluate-cli --help via {cli_help['method']}: {error_type}: {detail}")
    return 0 if cli_help["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
