#!/usr/bin/env python3
"""Build or compare Bindu DID signing payload strings without private keys."""
from __future__ import annotations
import argparse, json, sys, time

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--body", help="Literal request body string")
    src.add_argument("--body-file", help="Read exact body text from file")
    p.add_argument("--did", required=True)
    p.add_argument("--timestamp", type=int, default=None)
    p.add_argument("--compare", help="Optional payload string expected by another implementation")
    args = p.parse_args()
    body = open(args.body_file, 'rb').read().decode('utf-8') if args.body_file else args.body
    ts = args.timestamp if args.timestamp is not None else int(time.time())
    payload = json.dumps({"body": body, "timestamp": ts, "did": args.did}, sort_keys=True)
    print(payload)
    if args.compare is not None:
        ok = payload == args.compare
        print(f"compare_match={ok}", file=sys.stderr)
        return 0 if ok else 2
    return 0
if __name__ == "__main__": raise SystemExit(main())
