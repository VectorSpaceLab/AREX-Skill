#!/usr/bin/env python3
"""Minimal anomalib import smoke check."""

from __future__ import annotations

import json
from argparse import ArgumentParser


def main() -> int:
    parser = ArgumentParser(description="Check that anomalib imports and report its version.")
    parser.add_argument("--json", action="store_true", help="Print JSON output instead of plain text.")
    args = parser.parse_args()

    try:
        import anomalib
    except ImportError as exc:
        summary = {
            "package": "anomalib",
            "error": str(exc),
        }
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            print(
                "anomalib import failed; install the package or use the installed inspection environment"
            )
        return 1

    summary = {
        "package": "anomalib",
        "version": anomalib.__version__,
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"anomalib {anomalib.__version__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
