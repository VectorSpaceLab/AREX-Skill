#!/usr/bin/env python3
"""Inspect CogDL's default wrapper pair for one or more model names."""

from __future__ import annotations

import argparse
import json
from pprint import pprint


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", action="append", default=[], help="model name to inspect; may be repeated")
    parser.add_argument("--list", action="store_true", help="list the default wrapper table")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a pretty dict")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    from cogdl.wrappers.default_match import default_wrapper_config, get_wrappers_name

    models = args.model or ["gcn", "gin", "prone", "gatne", "stgcn"]
    payload = {
        "requested_models": models,
        "wrappers": {name: get_wrappers_name(name) for name in models},
    }
    if args.list:
        payload["default_wrapper_count"] = len(default_wrapper_config)
        payload["default_wrapper_names"] = sorted(default_wrapper_config)

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        pprint(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
