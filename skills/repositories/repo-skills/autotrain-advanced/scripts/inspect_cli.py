#!/usr/bin/env python3
"""Inspect AutoTrain Advanced CLI help through the current Python interpreter.

Examples:

    python skills/disco/autotrain-advanced/scripts/inspect_cli.py
    python skills/disco/autotrain-advanced/scripts/inspect_cli.py llm --help
    python skills/disco/autotrain-advanced/scripts/inspect_cli.py tools merge-llm-adapter --help
"""

from __future__ import annotations

import shlex
import subprocess
import sys


def main() -> int:
    args = sys.argv[1:] or ["--help"]
    cmd = [sys.executable, "-m", "autotrain.cli.autotrain", *args]
    print("+ " + " ".join(shlex.quote(part) for part in cmd), file=sys.stderr)
    return subprocess.run(cmd, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
