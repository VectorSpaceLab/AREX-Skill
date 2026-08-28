#!/usr/bin/env python3
"""Read-only DocsGPT HTTP readiness checks.

This helper uses only the Python standard library. It never writes server state.
Examples:
  python check_deployment.py --base-url http://localhost:7091
  DOCSGPT_API_KEY=... python check_deployment.py --base-url http://localhost:7091 --token-env DOCSGPT_API_KEY
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class Result:
    path: str
    status: int | None
    ok: bool
    detail: str


def fetch(base_url: str, path: str, timeout: float, token: str | None) -> Result:
    headers = {"Accept": "application/json", "User-Agent": "docsgpt-skill-check/1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(base_url.rstrip("/") + path, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(65536)
            detail = f"{len(body)} bytes"
            if body:
                try:
                    parsed = json.loads(body)
                    if isinstance(parsed, dict):
                        detail = "JSON keys: " + ", ".join(sorted(parsed)[:12])
                    elif isinstance(parsed, list):
                        detail = f"JSON list ({len(parsed)} items)"
                except (json.JSONDecodeError, UnicodeDecodeError):
                    detail = f"non-JSON body ({len(body)} bytes)"
            return Result(path, response.status, 200 <= response.status < 300, detail)
    except urllib.error.HTTPError as error:
        body = error.read(2048).decode("utf-8", "replace").replace("\n", " ")
        return Result(path, error.code, False, body[:240] or error.reason)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return Result(path, None, False, str(error))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:7091")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--token", help="Bearer token/API key; prefer --token-env on shared shells")
    parser.add_argument("--token-env", default="DOCSGPT_API_KEY")
    parser.add_argument(
        "--require-models",
        action="store_true",
        help="Fail when /v1/models cannot be read (normally optional without a token)",
    )
    args = parser.parse_args()
    token = args.token or os.getenv(args.token_env)

    checks = [
        ("/api/health", True),
        ("/api/config", True),
        ("/v1/models", args.require_models or bool(token)),
    ]
    failures = 0
    for path, required in checks:
        result = fetch(args.base_url, path, args.timeout, token)
        label = "PASS" if result.ok else ("FAIL" if required else "SKIP")
        status = result.status if result.status is not None else "network"
        print(f"[{label}] {path} status={status}: {result.detail}")
        if required and not result.ok:
            failures += 1

    if failures:
        print(f"{failures} required check(s) failed", file=sys.stderr)
        return 1
    print("Required read-only checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
