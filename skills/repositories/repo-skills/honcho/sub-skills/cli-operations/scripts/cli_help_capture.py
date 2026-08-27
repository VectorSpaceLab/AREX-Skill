#!/usr/bin/env python3
"""Capture Honcho CLI help output.

This is a safe inspection helper. It does not mutate any state.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


COMMANDS = [
    ["--help"],
    ["doctor", "--help"],
    ["config", "--help"],
    ["workspace", "--help"],
    ["peer", "--help"],
    ["session", "--help"],
    ["message", "--help"],
    ["conclusion", "--help"],
]


def _honcho_executable() -> str | None:
    exe = shutil.which("honcho")
    if exe:
        return exe
    sibling = Path(sys.executable).with_name("honcho")
    if sibling.exists():
        return str(sibling)
    return None


def _capture(cmd: list[str]) -> dict[str, Any]:
    exe = _honcho_executable()
    if not exe:
        return {"command": ["honcho", *cmd], "available": False}
    result = subprocess.run([exe, *cmd], capture_output=True, text=True)
    return {
        "command": ["honcho", *cmd],
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    report = [_capture(cmd) for cmd in COMMANDS]

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for item in report:
            print(" ".join(item["command"]))
            if item.get("available") is False:
                print("  honcho executable not found on PATH")
            else:
                print(f"  returncode={item['returncode']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
