#!/usr/bin/env python3
"""Inspect CogDL's model registry without loading datasets or training."""

from __future__ import annotations

import argparse
import json
from pprint import pprint


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contains", default=None, help="only show models whose names contain this substring")
    parser.add_argument("--prefix", default=None, help="only show models whose names start with this prefix")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a pretty dict")
    parser.add_argument("--show-count", action="store_true", help="include the total model count")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    from cogdl.models import SUPPORTED_MODELS

    names = sorted(SUPPORTED_MODELS)
    if args.contains:
        names = [name for name in names if args.contains in name]
    if args.prefix:
        names = [name for name in names if name.startswith(args.prefix)]

    payload = {"models": names}
    if args.show_count:
        payload["count"] = len(SUPPORTED_MODELS)

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        pprint(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
