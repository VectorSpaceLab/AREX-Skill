#!/usr/bin/env python3
"""Run the installed Memori CLI from a temporary working directory."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        proc = subprocess.run(
            [sys.executable, "-m", "memori"],
            cwd=Path(td),
            text=True,
            capture_output=True,
            check=False,
        )
    print(
        json.dumps(
            {
                "command": [sys.executable, "-m", "memori"],
                "exit_code": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
            indent=2,
            sort_keys=True,
        )
    )
    raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
