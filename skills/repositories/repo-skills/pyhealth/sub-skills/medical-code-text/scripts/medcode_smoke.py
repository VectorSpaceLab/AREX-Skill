#!/usr/bin/env python3
"""Inspect PyHealth medical-code APIs without forcing cache refresh/downloads."""
import argparse
import json
from pyhealth.medcode import InnerMap, CrossMap


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vocabulary", default=None, help="explicit local vocabulary to load")
    parser.add_argument("--source", default=None, help="source vocabulary for a cross-map")
    parser.add_argument("--target", default=None, help="target vocabulary for a cross-map")
    parser.add_argument("--code", default=None, help="code to look up/map")
    args = parser.parse_args()
    result = {"inner": None, "cross": None}
    if args.vocabulary:
        inner = InnerMap.load(args.vocabulary, refresh_cache=False)
        result["inner"] = {"vocabulary": args.vocabulary, "loaded": type(inner).__name__}
        if args.code:
            result["inner"]["lookup"] = inner.lookup(args.code)
    if bool(args.source) != bool(args.target):
        raise SystemExit("--source and --target must be supplied together")
    if args.source and args.target:
        cross = CrossMap.load(args.source, args.target, refresh_cache=False)
        result["cross"] = {"source": args.source, "target": args.target, "loaded": type(cross).__name__}
        if args.code:
            result["cross"]["mapping"] = cross.map(args.code)
    print(json.dumps(result, indent=2, default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
