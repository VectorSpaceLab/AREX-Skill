#!/usr/bin/env python3
"""Small PixelRAG search API smoke checker.

Checks /health and /status. If --query is supplied, also posts a text search.
It does not start a server, download models, or require non-stdlib packages.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def request_json(url: str, data: dict | None = None, timeout: float = 10.0) -> dict:
    body = None
    headers = {}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:30001", help="PixelRAG API base URL")
    parser.add_argument("--query", help="optional text query to POST to /search")
    parser.add_argument("--n-docs", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--min-vectors", type=int, default=0, help="fail if /status total_vectors is lower")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    try:
        health = request_json(base + "/health", timeout=args.timeout)
        print("health:", health)
        status = request_json(base + "/status", timeout=args.timeout)
        print("status:", json.dumps(status, indent=2)[:2000])
        vectors = int(status.get("total_vectors", 0))
        if vectors < args.min_vectors:
            raise SystemExit(f"total_vectors {vectors} < required {args.min_vectors}")
        if args.query:
            payload = {"queries": [{"text": args.query}], "n_docs": args.n_docs}
            result = request_json(base + "/search", payload, timeout=args.timeout)
            hits = result.get("results", [{}])[0].get("hits", [])
            print(f"search returned {len(hits)} hit(s)")
            for i, hit in enumerate(hits[: args.n_docs], 1):
                print(f"{i}. score={hit.get('score')} article_id={hit.get('article_id')} url={hit.get('url')}")
        return 0
    except urllib.error.URLError as exc:
        print(f"request failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
