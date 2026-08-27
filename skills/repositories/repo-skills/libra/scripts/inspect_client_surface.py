#!/usr/bin/env python3
"""Inspect the public `libra.client` surface."""
from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[3]
for candidate in (SCRIPT_DIR, REPO_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from libra_compat import apply


def main() -> int:
    parser = argparse.ArgumentParser(description='Inspect the public Libra client surface.')
    parser.add_argument('--json', action='store_true', help='Emit JSON instead of a text table.')
    parser.add_argument('--methods-only', action='store_true', help='Print only public method names.')
    args = parser.parse_args()

    apply()

    from libra import client
    apply()

    methods = [name for name in dir(client) if not name.startswith('_')]
    if args.methods_only:
        for name in methods:
            print(name)
        return 0

    entries = []
    for name in methods:
        attr = getattr(client, name)
        try:
            signature = str(inspect.signature(attr))
        except (TypeError, ValueError):
            signature = '<no signature>'
        entries.append({'name': name, 'signature': signature})

    if args.json:
        print(json.dumps(entries, indent=2, sort_keys=True))
    else:
        print('Public libra.client methods:')
        for entry in entries:
            print(f"- {entry['name']}{entry['signature']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
