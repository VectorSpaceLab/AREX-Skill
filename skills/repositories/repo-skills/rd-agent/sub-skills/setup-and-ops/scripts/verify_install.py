#!/usr/bin/env python3
"""Collect low-cost installation and CLI checks for an RD-Agent environment."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


COMMANDS = [
    [sys.executable, "-m", "pip", "check"],
    [sys.executable, "-c", "import rdagent; print(rdagent.__file__)"],
    ["rdagent", "--help"],
    ["rdagent", "health_check", "--no-check-env", "--no-check-docker"],
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()
    results = []
    for command in COMMANDS:
        try:
            proc = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
            results.append({"command": command, "returncode": proc.returncode, "stdout": proc.stdout[-1000:], "stderr": proc.stderr[-1000:]})
        except (OSError, subprocess.TimeoutExpired) as exc:
            results.append({"command": command, "error": str(exc)})
    print(json.dumps(results, indent=2))
    return 0 if all(item.get("returncode") == 0 for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
