#!/usr/bin/env python3
"""Check Mars supervisor and worker CLI help paths safely.

This helper does not start Mars services. It runs module-level `--help` commands
with the current Python interpreter, which works even when console scripts are
not on PATH.

Examples:
  python scripts/check_mars_cli.py
  python scripts/check_mars_cli.py --json

Run this file with the Python interpreter from the environment where `pymars` is
installed; the subprocess checks intentionally use that interpreter.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any, Dict

COMMANDS = {
    "mars-supervisor": [sys.executable, "-m", "mars.deploy.oscar.supervisor", "--help"],
    "mars-worker": [sys.executable, "-m", "mars.deploy.oscar.worker", "--help"],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON output")
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="per-command timeout in seconds",
    )
    return parser


def run_help(name: str, cmd: list[str], timeout: float) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - user-facing smoke path
        return {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
    first_lines = "\n".join(proc.stdout.splitlines()[:8])
    status = "ok" if proc.returncode == 0 and "usage:" in proc.stdout else "failed"
    return {
        "status": status,
        "returncode": proc.returncode,
        "first_lines": first_lines,
        "stderr": proc.stderr.strip()[:500],
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = {name: run_help(name, cmd, args.timeout) for name, cmd in COMMANDS.items()}
    ok = all(item["status"] == "ok" for item in result.values())
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for name, item in result.items():
            print(f"== {name}: {item['status']} ==")
            print(item.get("first_lines", ""))
            if item.get("stderr"):
                print(item["stderr"], file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
