#!/usr/bin/env python3
"""Safely audit RoboVerse package/task discovery without running a simulator.

This bundled helper replaces a source-repository registration diagnostic. It
checks imports and optionally resolves a task id; it does not download assets,
start a renderer, create a real robot connection, or claim backend parity.

Examples:
  python verify_registration.py
  python verify_registration.py --task benchmark.cube_reach
"""
from __future__ import annotations

import argparse
import importlib
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", help="Optional MetaSim/RoboVerse task id to resolve")
    args = parser.parse_args()

    try:
        importlib.import_module("roboverse_pack")
        metasim = importlib.import_module("metasim")
    except Exception as exc:  # diagnostic output should name the missing layer
        print(f"IMPORT_FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("Install roboverse-py with the selected MetaSim backend extra.", file=sys.stderr)
        return 2

    print(f"IMPORT_OK roboverse_pack + metasim ({getattr(metasim, '__version__', 'version unknown')})")
    if args.task:
        try:
            registry = importlib.import_module("metasim.task.registry")
            get_task_class = getattr(registry, "get_task_class")
            cls = get_task_class(args.task)
        except Exception as exc:
            print(f"TASK_RESOLVE_FAIL {args.task!r}: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 3
        print(f"TASK_OK {args.task} -> {cls.__module__}.{cls.__name__}")
    print("This audit proves imports/discovery only; run a bounded backend-specific reset before parity claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
