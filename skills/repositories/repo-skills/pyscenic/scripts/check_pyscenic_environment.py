#!/usr/bin/env python3
"""Check whether a Python environment can import and run pySCENIC safely.

This diagnostic is read-only. It imports key modules, checks distribution
metadata, and optionally runs CLI help commands. It does not download ranking
databases, run GRN inference, prune motifs, score AUCell, or write data files.
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

MODULES = [
    "pyscenic",
    "pyscenic.aucell",
    "pyscenic.binarization",
    "pyscenic.prune",
    "pyscenic.utils",
    "pyscenic.cli.pyscenic",
]

CLI_COMMANDS = [
    ["pyscenic", "--help"],
    ["pyscenic", "grn", "--help"],
    ["pyscenic", "add_cor", "--help"],
    ["pyscenic", "ctx", "--help"],
    ["pyscenic", "aucell", "--help"],
    ["arboreto_with_multiprocessing.py", "--help"],
]


def import_check() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for name in MODULES:
        try:
            module = importlib.import_module(name)
            results.append({"name": name, "ok": True, "file": getattr(module, "__file__", None)})
        except Exception as exc:
            results.append({"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    return results


def metadata_check() -> dict[str, Any]:
    try:
        return {"ok": True, "version": metadata.version("pyscenic")}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def cli_check(timeout: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for command in CLI_COMMANDS:
        executable = shutil.which(command[0])
        if executable is None:
            results.append({"command": command, "ok": False, "error": "executable not found on PATH"})
            continue
        try:
            proc = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
        except Exception as exc:
            results.append({"command": command, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
            continue
        results.append({
            "command": command,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout_first_line": proc.stdout.splitlines()[0] if proc.stdout.splitlines() else "",
            "stderr_first_line": proc.stderr.splitlines()[0] if proc.stderr.splitlines() else "",
        })
    return results


def advice(results: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    text = json.dumps(results)
    if "No module named 'pkg_resources'" in text:
        notes.append("ctxcore imports pkg_resources; install a setuptools release that still provides pkg_resources, then rerun this check.")
    if "No module named 'attr'" in text:
        notes.append("ctxcore imports attr; install attrs, then rerun this check.")
    if "No module named 'pyscenic'" in text:
        notes.append("Install pySCENIC in the active environment before running CLI or API workflows.")
    if "executable not found on PATH" in text:
        notes.append("At least one console script is missing from PATH; verify the active environment and package entry points.")
    return notes


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only pySCENIC environment diagnostic.")
    parser.add_argument("--check-cli", action="store_true", help="Also run safe CLI help checks.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout in seconds for each CLI help command.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a human-readable summary.")
    args = parser.parse_args()

    results: dict[str, Any] = {
        "python": sys.version.split()[0],
        "distribution": metadata_check(),
        "imports": import_check(),
    }
    if args.check_cli:
        results["cli"] = cli_check(args.timeout)
    results["advice"] = advice(results)

    ok = bool(results["distribution"]["ok"]) and all(item["ok"] for item in results["imports"])
    if args.check_cli:
        ok = ok and all(item["ok"] for item in results["cli"])
    results["ok"] = ok

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print(f"Python: {results['python']}")
        print(f"pySCENIC distribution: {results['distribution']}")
        for item in results["imports"]:
            print(("OK" if item["ok"] else "FAIL") + f" import {item['name']}" + (f" - {item.get('error')}" if not item["ok"] else ""))
        for item in results.get("cli", []):
            print(("OK" if item["ok"] else "FAIL") + " cli " + " ".join(item["command"]) + (f" - {item.get('error') or item.get('stderr_first_line')}" if not item["ok"] else ""))
        for note in results["advice"]:
            print(f"Advice: {note}")
        print("Environment ready: " + ("yes" if ok else "no"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
