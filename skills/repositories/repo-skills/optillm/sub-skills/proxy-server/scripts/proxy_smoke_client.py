#!/usr/bin/env python3
"""Build or send a minimal OptiLLM OpenAI-compatible chat request.

Dry-run is the default and performs no network call.

Examples:
  python proxy_smoke_client.py --model moa-gpt-4o-mini
  python proxy_smoke_client.py --approach re2 --model gpt-4o-mini --dry-run
  python proxy_smoke_client.py --send --base-url http://localhost:8000/v1 --api-key anything
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def build_payload(args: argparse.Namespace) -> dict:
    model = args.model
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": args.prompt}],
        "stream": args.stream,
        "n": args.n,
    }
    if args.approach:
        payload["optillm_approach"] = args.approach
    if args.max_tokens is not None:
        payload["max_tokens"] = args.max_tokens
    return payload


def send_payload(base_url: str, api_key: str, payload: dict, timeout: float) -> tuple[int, str]:
    url = base_url.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec: explicit user URL
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run or send an OptiLLM chat-completion smoke request")
    parser.add_argument("--base-url", default="http://localhost:8000/v1", help="OptiLLM OpenAI-compatible base URL")
    parser.add_argument("--api-key", default="anything", help="Server API key or placeholder")
    parser.add_argument("--model", default="gpt-4o-mini", help="Model string, optionally prefixed with an approach")
    parser.add_argument("--approach", help="Optional optillm_approach request field")
    parser.add_argument("--prompt", default="Say 'ok' in one short sentence.", help="User prompt")
    parser.add_argument("--n", type=int, default=1, help="Number of responses")
    parser.add_argument("--max-tokens", type=int, help="Optional max_tokens")
    parser.add_argument("--stream", action="store_true", help="Request streaming; not parsed by this helper")
    parser.add_argument("--send", action="store_true", help="Actually send the request; default is dry-run only")
    parser.add_argument("--dry-run", action="store_true", help="Explicitly request the default dry-run behavior")
    parser.add_argument("--timeout", type=float, default=30.0, help="Network timeout for --send")
    args = parser.parse_args()

    payload = build_payload(args)
    print(json.dumps({"base_url": args.base_url, "payload": payload}, indent=2))
    if not args.send:
        print("Dry-run only. Add --send to perform the request.", file=sys.stderr)
        return 0
    status, body = send_payload(args.base_url, args.api_key, payload, args.timeout)
    print(f"HTTP {status}")
    print(body)
    return 0 if 200 <= status < 300 else 1


if __name__ == "__main__":
    raise SystemExit(main())
