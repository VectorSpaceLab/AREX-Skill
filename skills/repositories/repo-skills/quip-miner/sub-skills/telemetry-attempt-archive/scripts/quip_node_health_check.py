#!/usr/bin/env python3
"""Check quip-miner telemetry endpoints without requiring jq or curl."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any


def fetch(base: str, path: str, timeout: float) -> tuple[int, dict[str, Any] | None, str]:
    url = base.rstrip("/") + path
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(body), ""
            except json.JSONDecodeError:
                return resp.status, None, body[:200]
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = None
        return exc.code, data, body[:200]
    except Exception as exc:  # noqa: BLE001
        return 0, None, f"{type(exc).__name__}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", help="Telemetry base URL, e.g. http://127.0.0.1:8086")
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    checks = [
        ("/health", {200}),
        ("/api/v1/status", {200, 503}),
        ("/api/v1/stats", {200, 503}),
        ("/api/v1/system", {200, 503}),
        ("/api/v1/miner/survey", {200, 503}),
        ("/api/v1/block/latest", {200, 502, 503}),
    ]
    failures = 0
    for path, acceptable in checks:
        code, data, err = fetch(args.base_url, path, args.timeout)
        ok = code in acceptable
        print(f"{'PASS' if ok else 'FAIL'} {path}: HTTP {code}")
        if args.verbose and data is not None:
            print(json.dumps(data, indent=2, sort_keys=True)[:2000])
        elif args.verbose and err:
            print(err)
        if not ok:
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
