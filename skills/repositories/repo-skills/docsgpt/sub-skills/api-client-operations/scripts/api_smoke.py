#!/usr/bin/env python3
"""Bounded DocsGPT API smoke client using only the standard library.

Default checks are read-only. Supplying --question sends a real /api/answer
request and may persist a hidden conversation; use only with a test agent.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def request(base: str, path: str, timeout: float, token: str | None, body: dict | None = None) -> tuple[int, object]:
    headers = {"Accept": "application/json", "User-Agent": "docsgpt-api-smoke/1"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(base.rstrip("/") + path, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read(1_000_000)
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        raw = error.read(65536)
        try:
            detail: object = json.loads(raw)
        except Exception:
            detail = raw.decode("utf-8", "replace")[:500]
        return error.code, detail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:7091")
    parser.add_argument("--token", help="Bearer agent key/JWT; prefer --token-env")
    parser.add_argument("--token-env", default="DOCSGPT_API_KEY")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--require-models", action="store_true")
    parser.add_argument("--question", help="Opt in to a real /api/answer call")
    parser.add_argument("--agent-key-env", default="DOCSGPT_AGENT_KEY")
    args = parser.parse_args()
    token = args.token or os.getenv(args.token_env)
    failures = 0

    for path, required in (("/api/health", True), ("/api/config", True), ("/v1/models", args.require_models)):
        try:
            status, payload = request(args.base_url, path, args.timeout, token)
            ok = 200 <= status < 300
            label = "PASS" if ok else ("FAIL" if required else "SKIP")
            summary = sorted(payload)[:10] if isinstance(payload, dict) else type(payload).__name__
            print(f"[{label}] GET {path}: HTTP {status}; {summary}")
            if required and not ok:
                failures += 1
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
            print(f"[{'FAIL' if required else 'SKIP'}] GET {path}: {error}")
            failures += int(required)

    if args.question:
        agent_key = os.getenv(args.agent_key_env)
        if not agent_key:
            print(f"FAIL: --question requires {args.agent_key_env}", file=sys.stderr)
            return 2
        body = {"question": args.question, "api_key": agent_key, "visibility": "hidden"}
        try:
            status, payload = request(args.base_url, "/api/answer", args.timeout, None, body)
            ok = 200 <= status < 300 and isinstance(payload, dict) and "answer" in payload
            print(f"[{'PASS' if ok else 'FAIL'}] POST /api/answer: HTTP {status}; keys={sorted(payload) if isinstance(payload, dict) else type(payload).__name__}")
            failures += not ok
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
            print(f"[FAIL] POST /api/answer: {error}")
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
