#!/usr/bin/env python3
"""Launch the Pyraformer long-range CLI from a repo checkout.

The wrapper keeps the source CLI authoritative. It only resolves the checkout
root, checks that the source entry point exists, and forwards every unknown flag
verbatim to `Pyraformer/long_range_main.py`.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

SOURCE_DIR = Path("Pyraformer")
SOURCE = SOURCE_DIR / "long_range_main.py"


def discover_repo_root(explicit: str | None) -> Path:
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not root.is_dir():
            raise SystemExit(f"Repo root does not exist: {root}")
        return root

    candidates = [Path.cwd().resolve(), *Path.cwd().resolve().parents, Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / SOURCE).is_file():
            return candidate

    raise SystemExit(
        "Could not find a checkout containing Pyraformer/long_range_main.py. "
        "Pass --repo-root to point at the LTSF-Linear checkout."
    )


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Launch Pyraformer long-range forecasting from a repo checkout."
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Root of the LTSF-Linear checkout. Defaults to the nearest parent containing Pyraformer/long_range_main.py.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable to use for the source CLI.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved command and exit without running it.",
    )
    args, extra = parser.parse_known_args()
    return args, extra


def main() -> int:
    args, extra = parse_args()
    root = discover_repo_root(args.repo_root)
    source = root / SOURCE
    if not source.is_file():
        raise SystemExit(f"Source entry point not found: {source}")

    command = [args.python, source.name, *extra]
    cwd = root / SOURCE_DIR
    print(f"[pyraformer-long] {shlex.join(command)}  (cwd={cwd})")
    if args.dry_run:
        return 0

    completed = subprocess.run(command, cwd=cwd)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
