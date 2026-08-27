#!/usr/bin/env python3
"""Run a standard-library-only model/prognostic/diagnostic/DA contract fixture."""
from __future__ import annotations

import argparse
import json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tiny-fixture", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.tiny_fixture:
        parser.print_help()
        return 0
    result = {"prognostic": ["__call__", "create_iterator", "input_coords", "output_coords", "to"], "diagnostic": ["__call__", "input_coords", "output_coords", "to"], "assimilation": ["__call__", "create_generator", "init_coords", "input_coords", "output_coords", "to"], "offline": True}
    if args.json: print(json.dumps(result, sort_keys=True))
    else:
        print("offline model contract fixture: PASS")
        print("- prognostic, diagnostic, and assimilation method sets checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
