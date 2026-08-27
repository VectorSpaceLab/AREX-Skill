#!/usr/bin/env python3
"""Dry-run or launch the checkout's TorchScript export CLI through a checked wrapper.

Safe by default:
- prints the command unless --execute is given
- requires an explicit --repo-root
- forwards all extra arguments after `--`
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    p = argparse.ArgumentParser(description="Launch BackgroundMattingV2 TorchScript export")
    p.add_argument("--repo-root", required=True)
    p.add_argument("--python", default=sys.executable)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args, remainder = p.parse_known_args()
    if remainder and remainder[0] == "--":
        remainder = remainder[1:]
    return args, remainder


def main() -> int:
    args, passthrough = parse_args()
    repo_root = Path(args.repo_root).resolve()
    script = repo_root / "export_torchscript.py"
    if not repo_root.exists():
        print(f"repo-root does not exist: {repo_root}", file=sys.stderr)
        return 2
    if not script.exists():
        print(f"TorchScript export entry not found: {script}", file=sys.stderr)
        return 3

    cmd = [args.python, str(script), *passthrough]
    print(shlex.join(cmd))
    if args.dry_run or not args.execute:
        return 0
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    raise SystemExit(main())
