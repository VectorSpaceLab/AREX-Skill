#!/usr/bin/env python3
"""Smoke-test a local OpenAI-compatible ms-swift deployment.

Defaults target http://127.0.0.1:8000/v1 and make no external network calls.
The script uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


def request_json(url: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None,
                 api_key: Optional[str] = None, timeout: float = 30.0) -> Dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        response_data = response.read().decode("utf-8")
    if not response_data:
        return {}
    return json.loads(response_data)


def normalize_base_url(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"
    return base_url


def fetch_models(base_url: str, api_key: Optional[str], timeout: float) -> List[str]:
    payload = request_json(f"{base_url}/models", api_key=api_key, timeout=timeout)
    models = [item.get("id") for item in payload.get("data", []) if item.get("id")]
    if not models:
        raise RuntimeError(f"No models returned from {base_url}/models: {payload}")
    return models


def chat_completion(base_url: str, api_key: Optional[str], model: str, prompt: str, max_tokens: int,
                    temperature: float, timeout: float) -> Dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }
    return request_json(f"{base_url}/chat/completions", method="POST", payload=payload, api_key=api_key, timeout=timeout)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test a local ms-swift OpenAI-compatible server.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1",
                        help="OpenAI-compatible base URL. Defaults to local ms-swift deploy.")
    parser.add_argument("--api-key", default="EMPTY", help="Bearer token. Use an empty string to omit auth header.")
    parser.add_argument("--model", help="Model id. Defaults to the first id from /v1/models.")
    parser.add_argument("--prompt", default="Reply with the word swift.")
    parser.add_argument("--max-tokens", type=int, default=16)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--skip-model-list", action="store_true",
                        help="Do not call /v1/models; requires --model.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_url = normalize_base_url(args.base_url)
    api_key = args.api_key or None

    try:
        if args.skip_model_list:
            if not args.model:
                raise RuntimeError("--skip-model-list requires --model")
            model = args.model
            models = [model]
        else:
            models = fetch_models(base_url, api_key, args.timeout)
            model = args.model or models[0]
            if model not in models:
                raise RuntimeError(f"Requested model {model!r} is not in server model list: {models}")

        response = chat_completion(
            base_url=base_url,
            api_key=api_key,
            model=model,
            prompt=args.prompt,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            timeout=args.timeout,
        )
        choices = response.get("choices") or []
        if not choices:
            raise RuntimeError(f"No choices returned: {response}")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if content is None:
            raise RuntimeError(f"No message content returned: {response}")

        print(json.dumps({"ok": True, "base_url": base_url, "model": model, "models": models, "content": content},
                         ensure_ascii=False, indent=2))
        return 0
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "base_url": base_url, "error": str(exc)}, ensure_ascii=False, indent=2),
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
