#!/usr/bin/env python3
"""Inspect Cognee's memory API surface safely.

This helper does not call external services or mutate data. It only verifies
that the installed `cognee` package exposes the expected memory entry points and
prints the installed signatures.
"""

from __future__ import annotations

import argparse
import inspect
import json


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Cognee memory APIs safely.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    args = parser.parse_args()

    import cognee

    names = ["remember", "recall", "add", "cognify", "search", "improve", "forget"]
    summary = {
        "version": getattr(cognee, "__version__", None),
        "signatures": {},
    }
    for name in names:
        obj = getattr(cognee, name)
        summary["signatures"][name] = str(inspect.signature(obj))

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Cognee version: {summary['version']}")
        for name in names:
            print(f"{name}: {summary['signatures'][name]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
