#!/usr/bin/env python3
"""Validate a VSE typoMap.json file."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

def main() -> int:
    ap=argparse.ArgumentParser(description='Lint VSE typoMap.json: JSON object plus compilable regex keys.')
    ap.add_argument('--typo-map', required=True, help='Path to typoMap.json or compatible JSON map.')
    args=ap.parse_args()
    path=Path(args.typo_map)
    try:
        data=json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        print(f'FAIL: cannot read JSON: {exc}', file=sys.stderr); return 2
    if not isinstance(data, dict):
        print('FAIL: typo map must be a JSON object', file=sys.stderr); return 2
    errors=[]
    for k,v in data.items():
        if not isinstance(k,str) or not isinstance(v,str):
            errors.append(f'non-string key/value: {k!r} -> {v!r}'); continue
        try: re.compile(k, re.I)
        except re.error as exc: errors.append(f'bad regex {k!r}: {exc}')
    if errors:
        print('FAIL:')
        for e in errors: print('-', e)
        return 1
    print(f'OK: {len(data)} typo replacement rule(s) are valid regex strings.')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
