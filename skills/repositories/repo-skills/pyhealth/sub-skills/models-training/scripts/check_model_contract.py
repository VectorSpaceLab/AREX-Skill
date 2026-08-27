#!/usr/bin/env python3
"""Check a JSON batch has fields required by a declared model contract."""
import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path, help="JSON object representing one batch")
    parser.add_argument("--require", action="append", default=[], help="required top-level key")
    args = parser.parse_args()
    data = json.loads(args.batch.read_text())
    if not isinstance(data, dict):
        raise SystemExit("batch must be a JSON object")
    missing = [key for key in args.require if key not in data]
    print(json.dumps({"keys": sorted(data), "missing": missing}, indent=2))
    return 0 if not missing else 1

if __name__ == "__main__":
    raise SystemExit(main())
