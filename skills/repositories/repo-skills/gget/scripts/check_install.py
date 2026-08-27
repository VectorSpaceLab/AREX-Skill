#!/usr/bin/env python3
"""Read-only gget installation and CLI diagnostic.

Run as ``python scripts/check_install.py`` from any working directory after
installing gget. It reports interpreter, distribution version, public import,
and safe CLI version/help status; it does not contact a database or write files.
"""
from __future__ import annotations

import importlib.metadata
import subprocess
import sys


def main() -> int:
    print(f"python: {sys.executable}")
    print(f"python_version: {sys.version.split()[0]}")
    try:
        version = importlib.metadata.version("gget")
    except importlib.metadata.PackageNotFoundError:
        print("gget_distribution: MISSING")
        return 1
    print(f"gget_distribution: {version}")
    try:
        import gget

        print(f"gget_import: OK ({gget.__version__})")
    except Exception as exc:  # noqa: BLE001 - diagnostic must show the cause
        print(f"gget_import: FAIL ({type(exc).__name__}: {exc})")
        return 1

    for args in ((sys.executable, "-m", "gget", "--version"), (sys.executable, "-m", "gget", "--help")):
        try:
            completed = subprocess.run(args, capture_output=True, text=True, timeout=15, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f"cli {' '.join(args[2:])}: FAIL ({exc})")
            return 1
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip().splitlines()
            print(f"cli {' '.join(args[2:])}: FAIL ({detail[-1] if detail else 'no output'})")
            return 1
        first_line = next((line.strip() for line in completed.stdout.splitlines() if line.strip()), "OK")
        print(f"cli {' '.join(args[2:])}: OK ({first_line[:160]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
