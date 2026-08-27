#!/usr/bin/env python3
"""Run selected non-hardware Mycodo checkout checks with timeouts.

This helper is intentionally narrow. It does not run manual hardware tests,
install dependencies, start services, run Docker, or execute backup/restore/
upgrade actions except for the safe version-check script.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

CHECKS = {
    "import-smoke": [
        [sys.executable, "-c", "import mycodo, mycodo.config; print(mycodo.config.MYCODO_VERSION)"],
    ],
    "upgrade-check": [
        [sys.executable, "mycodo/scripts/upgrade_check.py", "--min_python_version", "3.8"],
    ],
    "pytest-abstract-input": [
        [sys.executable, "-m", "pytest", "mycodo/tests/software_tests/test_inputs/test_abstract_input_class.py", "-q"],
    ],
    "pytest-custom-function-update": [
        [sys.executable, "-m", "pytest", "mycodo/tests/software_tests/test_mycodo_flask/test_utils_settings.py", "-q"],
    ],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run selected safe Mycodo checks from a checkout.")
    parser.add_argument("--repo-root", required=True, help="Path to a Mycodo checkout/install root.")
    parser.add_argument("--timeout", type=float, default=120.0, help="Timeout per command in seconds.")
    parser.add_argument("--list", action="store_true", help="List available checks and exit.")
    parser.add_argument("check", nargs="?", choices=sorted(CHECKS), help="Check to run.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing.")
    return parser


def format_cmd(cmd: List[str]) -> str:
    return " ".join(shlex.quote(part) for part in cmd)


def run_check(repo: Path, check: str, timeout: float, dry_run: bool) -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    rc = 0
    for cmd in CHECKS[check]:
        print(f"$ {format_cmd(cmd)}")
        if dry_run:
            continue
        proc = subprocess.run(cmd, cwd=str(repo), env=env, text=True, capture_output=True, timeout=timeout)
        if proc.stdout:
            print(proc.stdout, end="")
        if proc.stderr:
            print(proc.stderr, end="", file=sys.stderr)
        if proc.returncode != 0:
            rc = proc.returncode
            break
    return rc


def main() -> int:
    args = build_parser().parse_args()
    if args.list:
        print("Available checks:")
        for name in sorted(CHECKS):
            print(f"  {name}")
        return 0
    if not args.check:
        print("ERROR: provide a check name or --list", file=sys.stderr)
        return 2
    repo = Path(args.repo_root).expanduser().resolve()
    if not (repo / "mycodo").is_dir():
        print(f"ERROR: not a Mycodo root: {repo}", file=sys.stderr)
        return 2
    print("Selected Mycodo check runner")
    print("Hardware/manual tests, installers, services, Docker, backup, restore, and dependency installs are not run.")
    return run_check(repo, args.check, args.timeout, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
