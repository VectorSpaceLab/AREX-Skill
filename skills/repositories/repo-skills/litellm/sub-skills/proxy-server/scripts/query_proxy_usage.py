#!/usr/bin/env python3
"""List LiteLLM proxy models and optionally run a tiny completion."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query a LiteLLM proxy with an explicit token or the token saved by litellm-proxy login."
    )
    parser.add_argument("--base-url", default="http://localhost:4000")
    parser.add_argument("--api-key", default=None, help="Proxy virtual key or master key.")
    parser.add_argument("--api-key-env", default="LITELLM_API_KEY")
    parser.add_argument("--list-models", action="store_true", default=True)
    parser.add_argument("--completion-model", help="Optional model alias for a tiny completion request.")
    parser.add_argument("--prompt", default="Reply with the single word pong.")
    parser.add_argument("--max-tokens", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--no-cli-token",
        action="store_true",
        help="Do not fall back to litellm.get_litellm_gateway_api_key().",
    )
    return parser.parse_args()


def load_api_key(args: argparse.Namespace) -> str:
    if args.api_key:
        return args.api_key
    env_value = os.environ.get(args.api_key_env)
    if env_value:
        return env_value
    if args.no_cli_token:
        return ""
    try:
        import litellm

        return litellm.get_litellm_gateway_api_key() or ""
    except Exception:
        return ""


def require_litellm() -> Any:
    try:
        import litellm

        return litellm
    except ImportError as exc:
        raise SystemExit("Install litellm before running this script.") from exc


def list_models(litellm_module: Any, base_url: str, api_key: str) -> list[str]:
    return litellm_module.get_valid_models(
        check_provider_endpoint=True,
        custom_llm_provider="litellm_proxy",
        api_key=api_key,
        api_base=base_url,
    )


def run_completion(
    litellm_module: Any,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    max_tokens: int,
) -> dict[str, Any]:
    response = litellm_module.completion(
        model=f"litellm_proxy/{model}",
        messages=[{"role": "user", "content": prompt}],
        api_key=api_key,
        base_url=base_url,
        max_tokens=max_tokens,
    )
    if hasattr(response, "model_dump"):
        return response.model_dump()
    return dict(response)


def main() -> None:
    args = parse_args()
    api_key = load_api_key(args)
    if not api_key:
        print(
            f"No proxy token found. Pass --api-key, set {args.api_key_env}, or run litellm-proxy login.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    litellm_module = require_litellm()
    base_url = args.base_url.rstrip("/")
    output: dict[str, Any] = {"base_url": base_url}

    if args.list_models:
        output["models"] = list_models(litellm_module, base_url, api_key)

    if args.completion_model:
        output["completion"] = run_completion(
            litellm_module,
            base_url,
            api_key,
            args.completion_model,
            args.prompt,
            args.max_tokens,
        )

    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True, default=str))
        return

    models = output.get("models") or []
    print(f"Proxy: {base_url}")
    print(f"Models ({len(models)}):")
    for index, model in enumerate(models, 1):
        print(f"  {index:2d}. {model}")
    if "completion" in output:
        print(json.dumps(output["completion"], indent=2, default=str))


if __name__ == "__main__":
    main()
