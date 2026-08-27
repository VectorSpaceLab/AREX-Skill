#!/usr/bin/env python3
"""Validate a local PyHealth data root without opening or downloading clinical data."""
import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="local dataset directory")
    parser.add_argument("--require", action="append", default=[], metavar="NAME", help="required relative file or directory")
    args = parser.parse_args()
    root = Path(args.root).expanduser()
    result = {"root": str(root), "exists": root.exists(), "is_directory": root.is_dir(), "required": {}}
    if not root.is_dir():
        print(json.dumps(result, indent=2)); return 1
    for item in args.require:
        result["required"][item] = (root / item).exists()
    print(json.dumps(result, indent=2))
    return 0 if all(result["required"].values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())
