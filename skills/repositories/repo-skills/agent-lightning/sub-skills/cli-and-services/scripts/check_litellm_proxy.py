#!/usr/bin/env python3
"""Safely check an OpenAI-compatible or LiteLLM proxy endpoint.

The script makes network requests only when endpoint arguments are supplied. It
never prints API keys. Use it for Agent Lightning LLMProxy, LiteLLM, vLLM, or
other OpenAI-compatible services.

Examples:
    python scripts/check_litellm_proxy.py --help
    python scripts/check_litellm_proxy.py --base-url http://127.0.0.1:8082/v1 --list-models --api-key dummy
    python scripts/check_litellm_proxy.py --base-url http://127.0.0.1:8082/v1 --model my-model --chat --api-key dummy
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List


def _client(base_url: str, api_key: str, timeout: float):
    try:
        from openai import OpenAI
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise RuntimeError("openai package is required for endpoint checks") from exc
    return OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check an OpenAI-compatible / LiteLLM proxy endpoint.")
    parser.add_argument("--base-url", required=True, help="OpenAI-compatible base URL, usually ending in /v1.")
    parser.add_argument("--api-key", default=None, help="API key; omitted output will never print it.")
    parser.add_argument("--api-key-env", default=None, help="Environment variable containing the API key.")
    parser.add_argument("--model", help="Model to call for chat/responses checks.")
    parser.add_argument("--list-models", action="store_true", help="Call models.list() and print model IDs.")
    parser.add_argument("--chat", action="store_true", help="Run a tiny chat.completions request.")
    parser.add_argument("--responses", action="store_true", help="Run a tiny responses.create request.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Request timeout in seconds.")
    args = parser.parse_args()

    api_key = args.api_key
    if api_key is None and args.api_key_env:
        api_key = os.getenv(args.api_key_env)
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY") or "dummy-key"

    if (args.chat or args.responses) and not args.model:
        parser.error("--model is required for --chat or --responses")

    if not (args.list_models or args.chat or args.responses):
        # Default to a chat smoke when a model is supplied, otherwise list models.
        if args.model:
            args.chat = True
        else:
            args.list_models = True

    try:
        client = _client(args.base_url, api_key, args.timeout)
    except RuntimeError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    failures: List[str] = []

    if args.list_models:
        try:
            models = client.models.list()
            model_ids = [model.id for model in models.data]
            print("PASS models:", ", ".join(model_ids) if model_ids else "<empty>")
        except Exception as exc:
            failures.append(f"models.list failed: {type(exc).__name__}: {exc}")

    if args.chat:
        try:
            response = client.chat.completions.create(
                model=args.model,
                messages=[{"role": "user", "content": "Say 'ok' in one word."}],
                temperature=0,
                max_tokens=8,
            )
            content = response.choices[0].message.content or ""
            print(f"PASS chat model={args.model} content={content[:80]!r}")
        except Exception as exc:
            failures.append(f"chat.completions failed: {type(exc).__name__}: {exc}")

    if args.responses:
        try:
            response = client.responses.create(model=args.model, input="Say ok in one word.")
            print(f"PASS responses model={args.model} id={getattr(response, 'id', '<no-id>')}")
        except Exception as exc:
            failures.append(f"responses.create failed: {type(exc).__name__}: {exc}")

    if failures:
        for failure in failures:
            print("FAIL", failure, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
