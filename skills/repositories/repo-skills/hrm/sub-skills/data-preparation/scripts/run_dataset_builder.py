#!/usr/bin/env python3
"""Run an HRM dataset builder through an explicit repo root.

This bundled wrapper keeps future-agent commands stable and avoids relying on a
current working directory. It forwards remaining arguments to the selected HRM
builder script in a user-provided checkout.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

BUILDERS = {
    "arc": Path("dataset/build_arc_dataset.py"),
    "sudoku": Path("dataset/build_sudoku_dataset.py"),
    "maze": Path("dataset/build_maze_dataset.py"),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one HRM dataset builder from an explicit checkout.")
    parser.add_argument("--repo-root", type=Path, required=True, help="Path to an HRM checkout.")
    parser.add_argument("--builder", choices=sorted(BUILDERS), required=True, help="Dataset builder to run.")
    parser.add_argument("builder_args", nargs=argparse.REMAINDER, help="Arguments forwarded after an optional `--` separator.")
    args = parser.parse_args()

    repo_root = args.repo_root.expanduser().resolve()
    script = repo_root / BUILDERS[args.builder]
    if not script.exists():
        print(f"ERROR: missing HRM builder script: {script}", file=sys.stderr)
        return 2
    forwarded = list(args.builder_args)
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.fspath(repo_root) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.call([sys.executable, os.fspath(script), *forwarded], cwd=os.fspath(repo_root), env=env)


if __name__ == "__main__":
    raise SystemExit(main())
