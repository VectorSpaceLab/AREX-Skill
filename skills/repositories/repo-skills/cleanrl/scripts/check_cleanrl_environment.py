#!/usr/bin/env python3
"""Check CleanRL importability and representative CLI help without training.

Example:
    python scripts/check_cleanrl_environment.py --check-help
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import subprocess
import sys
from pathlib import Path


def check_import(name: str) -> dict[str, object]:
    try:
        module = importlib.import_module(name)
        return {"name": name, "ok": True, "file": getattr(module, "__file__", None)}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def check_distribution(name: str) -> dict[str, object]:
    try:
        return {"name": name, "ok": True, "version": metadata.version(name)}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def run_help(script: str, timeout: int) -> dict[str, object]:
    path = Path(script)
    if not path.exists():
        return {"script": script, "ok": False, "error": "script not found from current working directory"}
    try:
        proc = subprocess.run(
            [sys.executable, script, "--help"],
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"script": script, "ok": False, "error": f"timed out after {timeout}s"}
    return {
        "script": script,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_head": proc.stdout[:1200],
        "stderr_head": proc.stderr[:1200],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check CleanRL imports and safe CLI help.")
    parser.add_argument("--check-help", action="store_true", help="run representative --help checks without training")
    parser.add_argument("--timeout", type=int, default=60, help="timeout per help check in seconds")
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()

    result: dict[str, object] = {
        "python": sys.version,
        "distributions": [check_distribution(name) for name in ["cleanrl", "torch", "gym", "gymnasium", "tyro", "wandb"]],
        "imports": [check_import(name) for name in ["cleanrl", "cleanrl_utils", "torch", "gym", "gymnasium", "tyro", "wandb"]],
        "help_checks": [],
    }
    if args.check_help:
        result["help_checks"] = [
            run_help(script, args.timeout)
            for script in ["cleanrl/ppo.py", "cleanrl/dqn.py", "cleanrl/c51.py", "cleanrl_utils/enjoy.py", "cleanrl_utils/benchmark.py"]
        ]

    ok = all(item["ok"] for item in result["distributions"]) and all(item["ok"] for item in result["imports"])
    if args.check_help:
        ok = ok and all(item["ok"] for item in result["help_checks"])
    result["ok"] = ok

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
        if not ok:
            print("CleanRL environment check failed; inspect JSON for missing imports, distributions, or help checks.", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
