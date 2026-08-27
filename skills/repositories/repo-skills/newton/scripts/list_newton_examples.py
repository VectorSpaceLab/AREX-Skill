#!/usr/bin/env python3
"""List examples exposed by the installed Newton package.

This wrapper uses the public `newton.examples` module and performs no simulation
unless `--run-help` is requested, in which case it only prints help for a named
example.
"""

from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="List installed Newton examples or show help for one example.")
    parser.add_argument("--run-help", metavar="EXAMPLE", help="Show help for a specific example via python -m newton.examples EXAMPLE --help.")
    parser.add_argument("--limit", type=int, default=0, help="Limit list output to the first N examples; 0 means all.")
    args = parser.parse_args()

    try:
        import newton.examples as examples
    except ModuleNotFoundError as exc:
        print(f"ERROR: cannot import Newton examples because {exc.name!r} is missing.")
        print("Install example dependencies with: pip install 'newton[examples]' when you need viewer/importer examples.")
        return 2

    if args.run_help:
        cmd = [sys.executable, "-m", "newton.examples", args.run_help, "--help"]
        try:
            completed = subprocess.run(cmd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20)
        except subprocess.TimeoutExpired:
            print("ERROR: example help command timed out; do not run the full example until dependencies are clear.")
            return 3
        print(completed.stdout, end="")
        return completed.returncode

    example_map = examples.get_examples()
    names = sorted(example_map)
    if args.limit > 0:
        names = names[: args.limit]
    for name in names:
        print(name)
    print(f"count={len(example_map)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
