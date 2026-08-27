#!/usr/bin/env python3
"""No-server PyRIT CLI smoke helper.

Runs only --help checks for installed console entry points. It does not start
pyrit_backend, contact a server, or run scans.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess

COMMANDS = ["pyrit_scan", "pyrit_shell", "pyrit_backend"]


def run_help(command: str, timeout: float) -> dict[str, object]:
    exe = shutil.which(command)
    if not exe:
        return {"command": command, "ok": False, "error": "not found on PATH"}
    proc = subprocess.run([exe, "--help"], capture_output=True, text=True, timeout=timeout, check=False)
    return {
        "command": command,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "first_line": (proc.stdout or proc.stderr).splitlines()[0] if (proc.stdout or proc.stderr) else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run help-only checks for PyRIT console scripts.")
    parser.add_argument("--timeout", type=float, default=10.0, help="timeout per --help command in seconds")
    parser.add_argument("--json", action="store_true", help="print JSON output")
    args = parser.parse_args()
    checks = []
    for command in COMMANDS:
        try:
            checks.append(run_help(command, args.timeout))
        except Exception as exc:  # noqa: BLE001
            checks.append({"command": command, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    ok = all(item.get("ok") for item in checks)
    result = {"ok": ok, "checks": checks, "note": "help-only; no backend started and no scan executed"}
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else result)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
