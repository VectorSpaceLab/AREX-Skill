#!/usr/bin/env python3
"""Safely inspect a TRL installation without training, downloads, or service startup.

Example:
    python check_trl_environment.py --json --optional peft --optional vllm
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


def check_import(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "file": getattr(module, "__file__", None)}


def check_distribution(name: str) -> dict[str, Any]:
    try:
        return {"ok": True, "version": metadata.version(name)}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def run_help(command: list[str]) -> dict[str, Any]:
    executable = shutil.which(command[0])
    if executable is None:
        return {"ok": False, "error": f"missing executable: {command[0]}"}
    try:
        completed = subprocess.run([executable, *command[1:]], text=True, capture_output=True, timeout=30)
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout_head": completed.stdout[:800],
        "stderr_head": completed.stderr[:800],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check TRL import, metadata, CLI help, and optional packages safely.")
    parser.add_argument("--optional", action="append", default=[], help="Optional import/package name to check, repeatable.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    report = {
        "python": sys.version.split()[0],
        "distributions": {name: check_distribution(name) for name in ["trl", "transformers", "accelerate", "datasets", "torch"]},
        "imports": {name: check_import(name) for name in ["trl", "trl.trainer", "trl.data_utils", "trl.rewards"]},
        "cli": {label: run_help(cmd) for label, cmd in {
            "trl --help": ["trl", "--help"],
            "trl env --help": ["trl", "env", "--help"],
            "trl sft --help": ["trl", "sft", "--help"],
            "trl grpo --help": ["trl", "grpo", "--help"],
        }.items()},
        "optional": {name: {"import": check_import(name), "distribution": check_distribution(name)} for name in args.optional},
    }
    ok = all(item["ok"] for item in report["imports"].values()) and report["distributions"]["trl"]["ok"]
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"TRL environment: {'ok' if ok else 'problem'}")
        for name, result in report["distributions"].items():
            print(f"{name}: {result.get('version') if result.get('ok') else result.get('error')}")
        for label, result in report["cli"].items():
            print(f"{label}: {'ok' if result.get('ok') else result.get('error', result.get('returncode'))}")
        for name, result in report["optional"].items():
            print(f"optional {name}: import={result['import'].get('ok')} distribution={result['distribution'].get('ok')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
