#!/usr/bin/env python3
"""HTTP preflight checker for PixelRAG eval services.

Checks an OpenAI-compatible reader /v1/models endpoint and one or more PixelRAG
search /status endpoints. It does not launch services, download indexes, call
LLM providers, or run benchmarks.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def get_json(url: str, timeout: float) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_reader(reader_url: str, expected: str | None, timeout: float) -> bool:
    base = reader_url.rstrip("/")
    if base.endswith("/v1"):
        url = base + "/models"
    else:
        url = base + "/v1/models"
    try:
        data = get_json(url, timeout)
    except Exception as exc:
        print(f"FAIL reader {url}: {exc}")
        return False
    text = json.dumps(data)
    ok = expected is None or expected in text
    print(("ok" if ok else "FAIL"), "reader", url)
    if expected and not ok:
        print(f"  expected model substring: {expected}")
    return ok


def check_search(spec: str, timeout: float) -> bool:
    # spec format: name=url[,min_vectors]
    name, rest = spec.split("=", 1)
    if "," in rest:
        url, min_s = rest.rsplit(",", 1)
        min_vectors = int(min_s)
    else:
        url, min_vectors = rest, 0
    status_url = url.rstrip("/").removesuffix("/search") + "/status"
    try:
        data = get_json(status_url, timeout)
        vectors = int(data.get("total_vectors", 0))
    except Exception as exc:
        print(f"FAIL {name} {status_url}: {exc}")
        return False
    ok = vectors >= min_vectors
    print(("ok" if ok else "FAIL"), name, status_url, f"vectors={vectors}", f"min={min_vectors}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reader-url", default="http://localhost:8010/v1")
    parser.add_argument("--expected-reader", default="Qwen/Qwen3.5-4B")
    parser.add_argument("--search", action="append", default=[], help="name=url[,min_vectors]; may repeat")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()

    ok = check_reader(args.reader_url, args.expected_reader, args.timeout)
    for spec in args.search:
        ok = check_search(spec, args.timeout) and ok
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
