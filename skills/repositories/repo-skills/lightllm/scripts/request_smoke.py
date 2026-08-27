#!/usr/bin/env python3
"""Send one tiny LightLLM request against a running local server."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

import requests


def build_payload(mode: str, model: str, prompt: str, max_tokens: int, stream: bool) -> tuple[str, Dict[str, Any]]:
    if mode == "generate":
        return "/generate", {"inputs": prompt, "parameters": {"max_new_tokens": max_tokens, "stream": stream}}
    if mode == "completions":
        return "/v1/completions", {"model": model, "prompt": prompt, "max_tokens": max_tokens, "stream": stream}
    if mode == "chat":
        return "/v1/chat/completions", {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "stream": stream,
        }
    if mode == "messages":
        return "/v1/messages", {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "stream": stream,
        }
    raise ValueError(f"unsupported mode: {mode}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="base URL for the local server")
    parser.add_argument("--mode", choices=["generate", "completions", "chat", "messages"], default="generate")
    parser.add_argument("--model", default="test-model", help="model name for OpenAI-style requests")
    parser.add_argument("--prompt", default="Hello", help="tiny prompt to send")
    parser.add_argument("--max-tokens", type=int, default=16, help="small generation budget")
    parser.add_argument("--stream", action="store_true", help="request streaming output")
    parser.add_argument("--timeout", type=float, default=30.0, help="request timeout in seconds")
    args = parser.parse_args()

    path, payload = build_payload(args.mode, args.model, args.prompt, args.max_tokens, args.stream)
    url = args.url.rstrip("/") + path
    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=args.timeout, stream=args.stream)
    except Exception as exc:
        print(f"request failed: {exc}", file=sys.stderr)
        return 1

    print(f"status={resp.status_code}")
    if args.stream:
        try:
            for line in resp.iter_lines():
                if line:
                    print(line.decode("utf-8", errors="replace"))
        finally:
            resp.close()
    else:
        ctype = resp.headers.get("content-type", "")
        print(f"content-type={ctype}")
        if "json" in ctype.lower():
            try:
                print(json.dumps(resp.json(), indent=2, sort_keys=True, ensure_ascii=False))
            except Exception:
                print(resp.text)
        else:
            print(resp.text)
    return 0 if resp.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
