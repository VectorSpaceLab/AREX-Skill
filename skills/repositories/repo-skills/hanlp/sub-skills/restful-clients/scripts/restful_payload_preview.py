#!/usr/bin/env python3
"""Build and validate a HanLP RESTful /parse payload without network calls."""
from __future__ import annotations
import argparse, json, sys

def csv(v): return [x.strip() for x in v.split(',') if x.strip()] if v else None

def main():
    ap = argparse.ArgumentParser(description="Preview a HanLP RESTful /parse JSON payload without sending it.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--text"); g.add_argument("--text-json"); g.add_argument("--tokens-json")
    ap.add_argument("--tasks"); ap.add_argument("--skip-tasks"); ap.add_argument("--language")
    a = ap.parse_args()
    payload = {"text": None, "tokens": None, "tasks": csv(a.tasks), "skip_tasks": csv(a.skip_tasks), "language": a.language}
    if a.text is not None: payload["text"] = a.text
    elif a.text_json is not None: payload["text"] = json.loads(a.text_json)
    else:
        payload["tokens"] = json.loads(a.tokens_json)
        if not isinstance(payload["tokens"], list) or any(not isinstance(s, list) for s in payload["tokens"]):
            raise SystemExit("--tokens-json must be a JSON list of token lists")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("POST this JSON body to <base-url>/parse when network/auth are available.", file=sys.stderr)
    return 0
if __name__ == "__main__": raise SystemExit(main())
