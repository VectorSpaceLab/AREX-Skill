#!/usr/bin/env python3
"""Lightweight smoke for the Pyraformer route.

The smoke checks only command-line reachability and the bundled preprocessing
helper in dry-run mode. It does not attempt a full training forward pass.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
SOURCE_DIR = Path("Pyraformer")


def discover_repo_root(explicit: str | None) -> Path:
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not root.is_dir():
            raise SystemExit(f"Repo root does not exist: {root}")
        return root

    candidates = [Path.cwd().resolve(), *Path.cwd().resolve().parents, SKILL_DIR, *SKILL_DIR.parents]
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / SOURCE_DIR / "long_range_main.py").is_file() and (candidate / SOURCE_DIR / "single_step_main.py").is_file():
            return candidate

    raise SystemExit(
        "Could not find a checkout containing the Pyraformer source entry points. "
        "Pass --repo-root to point at the LTSF-Linear checkout."
    )


def run_step(command: list[str], cwd: Path, label: str) -> int:
    print(f"[pyraformer-smoke] {label}")
    print(f"  cmd: {shlex.join(command)}")
    print(f"  cwd: {cwd}")
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if completed.stdout:
        print("  stdout:")
        for line in completed.stdout.rstrip().splitlines():
            print(f"    {line}")
    if completed.stderr:
        print("  stderr:")
        for line in completed.stderr.rstrip().splitlines():
            print(f"    {line}")
    if completed.returncode == 0:
        print("  status: ok")
    else:
        print(f"  status: failed ({completed.returncode})")
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke the Pyraformer route with help and dry-run checks.")
    parser.add_argument("--repo-root", type=str, default=None, help="Root of the LTSF-Linear checkout.")
    parser.add_argument("--python", default=sys.executable, help="Python executable to use.")
    args = parser.parse_args()

    repo_root = discover_repo_root(args.repo_root)
    pyraformer_dir = repo_root / SOURCE_DIR
    helper = SKILL_DIR / "prepare_pyraformer_data.py"

    steps = [
        ([args.python, "long_range_main.py", "--help"], pyraformer_dir, "source long-range help"),
        ([args.python, "single_step_main.py", "--help"], pyraformer_dir, "source single-step help"),
        ([args.python, str(helper), "--help"], repo_root, "bundled preprocessing help"),
        ([args.python, str(helper), "--dry-run", "synthetic", "--output-file", "data/synthetic.npy"], repo_root, "bundled synthetic dry-run"),
    ]

    failures = 0
    for command, cwd, label in steps:
        failures += 1 if run_step(command, cwd, label) != 0 else 0

    if failures:
        print(f"[pyraformer-smoke] {failures} step(s) failed")
        return 1

    print("[pyraformer-smoke] all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
