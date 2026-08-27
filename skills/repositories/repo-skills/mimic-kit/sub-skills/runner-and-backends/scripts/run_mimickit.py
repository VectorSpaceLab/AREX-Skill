#!/usr/bin/env python3
"""Dispatch MimicKit's target-checkout runner through a bundled skill wrapper.

Use this wrapper when a generated skill recipe needs to launch ``mimickit/run.py``
from a user-selected MimicKit checkout. The wrapper keeps the checkout root
explicit, prepares the repo-style ``PYTHONPATH`` expected by MimicKit's script
imports, and can print the final command without running it.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path


REQUIRED_RUNNER = Path("mimickit") / "run.py"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a target MimicKit checkout's runner with an explicit repo root.",
        epilog="Put MimicKit runner flags after '--', for example: -- --arg_file args/deepmimic_humanoid_ppo_args.txt --visualize false",
    )
    parser.add_argument("--repo-root", required=True, help="Target MimicKit checkout root")
    parser.add_argument("--python", default=sys.executable, help="Python executable used to launch the target runner")
    parser.add_argument("--dry-run", action="store_true", help="Print the command and environment changes without executing")
    parser.add_argument("runner_args", nargs=argparse.REMAINDER, help="Arguments passed through to mimickit/run.py after '--'")
    return parser


def normalize_runner_args(values: list[str]) -> list[str]:
    if values and values[0] == "--":
        return values[1:]
    return values


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).expanduser().resolve()
    runner = repo_root / REQUIRED_RUNNER
    if not repo_root.is_dir():
        print(f"error: --repo-root is not a directory: {repo_root}", file=sys.stderr)
        return 2
    if not runner.is_file():
        print(f"error: target checkout is missing {REQUIRED_RUNNER.as_posix()}: {repo_root}", file=sys.stderr)
        return 2

    runner_args = normalize_runner_args(args.runner_args)
    command = [args.python, str(runner), *runner_args]

    env = os.environ.copy()
    path_items = [str(repo_root / "mimickit"), str(repo_root)]
    old_pythonpath = env.get("PYTHONPATH")
    if old_pythonpath:
        path_items.append(old_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(path_items)

    printable = " ".join(shlex.quote(part) for part in command)
    print(f"MimicKit runner command: {printable}")
    print(f"Working directory: {repo_root}")
    print("PYTHONPATH prepended: <repo-root>/mimickit:<repo-root>")

    if args.dry_run:
        return 0

    completed = subprocess.run(command, cwd=str(repo_root), env=env)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
