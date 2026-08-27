#!/usr/bin/env python3
"""Run safe LiteLLM proxy health checks against selected models."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import TypedDict

import httpx

try:
    import yaml
except ImportError:
    yaml = None


class ModelInfo(TypedDict):
    id: str
    mode: str
    provider: str


class HealthResult(TypedDict, total=False):
    model: str
    healthy: bool
    error: str | None
    response_time_ms: float | None
    mode: str
    response_preview: str
    dimensions: int


DEFAULT_CHAT_PROMPT = "Reply with the single word healthy."
DEFAULT_EMBEDDING_TEXT = "LiteLLM proxy embedding health check."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check selected models on a LiteLLM proxy using short, safe requests."
    )
    parser.add_argument("--base-url", default="http://localhost:4000")
    parser.add_argument("--api-key", default=None, help="Proxy virtual key or master key.")
    parser.add_argument(
        "--api-key-env",
        default="LITELLM_API_KEY",
        help="Environment variable fallback for --api-key.",
    )
    parser.add_argument("--config", type=Path, help="Optional LiteLLM config.yaml to read model_list from.")
    parser.add_argument("--models", nargs="*", help="Optional allowlist of model aliases to check.")
    parser.add_argument("--auth-header", default="Authorization")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--chat-prompt", default=DEFAULT_CHAT_PROMPT)
    parser.add_argument("--embedding-text", default=DEFAULT_EMBEDDING_TEXT)
    parser.add_argument("--max-concurrency", type=int, default=4)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--fail-on-unhealthy",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Exit non-zero when any checked model is unhealthy.",
    )
    return parser.parse_args()


def resolve_api_key(args: argparse.Namespace) -> str:
    if args.api_key:
        return args.api_key
    import os

    return os.environ.get(args.api_key_env, "")


def build_headers(api_key: str, auth_header: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        header_value = f"Bearer {api_key}"
        headers[auth_header] = header_value
    return headers


def load_models_from_yaml(config_path: Path) -> list[ModelInfo]:
    if yaml is None:
        raise SystemExit("PyYAML is required for --config. Install litellm[proxy] or PyYAML.")
    raw_config = yaml.safe_load(config_path.read_text()) or {}
    model_entries = raw_config.get("model_list") or []
    models: list[ModelInfo] = []
    for entry in model_entries:
        model_name = entry.get("model_name")
        if not model_name:
            continue
        litellm_params = entry.get("litellm_params") or {}
        model_info = litellm_params.get("model_info") or entry.get("model_info") or {}
        models.append(
            {
                "id": str(model_name),
                "mode": str(model_info.get("mode") or "").lower(),
                "provider": str(model_info.get("provider") or ""),
            }
        )
    return models


async def fetch_models(client: httpx.AsyncClient, base_url: str, headers: dict[str, str]) -> list[ModelInfo]:
    response = await client.get(f"{base_url}/v1/models", headers=headers)
    response.raise_for_status()
    data = response.json()
    return [
        {"id": str(model.get("id")), "mode": "", "provider": ""}
        for model in data.get("data", [])
        if model.get("id")
    ]


def is_embedding_model(model: ModelInfo) -> bool:
    model_id = model["id"].lower()
    return model.get("mode") == "embedding" or "embedding" in model_id or "embed" in model_id


async def check_model(
    client: httpx.AsyncClient,
    base_url: str,
    headers: dict[str, str],
    model: ModelInfo,
    chat_prompt: str,
    embedding_text: str,
    semaphore: asyncio.Semaphore,
) -> HealthResult:
    async with semaphore:
        started = time.perf_counter()
        result: HealthResult = {
            "model": model["id"],
            "healthy": False,
            "error": None,
            "response_time_ms": None,
            "mode": model.get("mode", ""),
        }
        try:
            if is_embedding_model(model):
                response = await client.post(
                    f"{base_url}/v1/embeddings",
                    headers=headers,
                    json={"model": model["id"], "input": embedding_text},
                )
                response.raise_for_status()
                payload = response.json()
                embedding = (payload.get("data") or [{}])[0].get("embedding") or []
                result["mode"] = "embedding"
                result["dimensions"] = len(embedding)
            else:
                response = await client.post(
                    f"{base_url}/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": model["id"],
                        "messages": [{"role": "user", "content": chat_prompt}],
                        "max_tokens": 10,
                    },
                )
                response.raise_for_status()
                payload = response.json()
                content = (((payload.get("choices") or [{}])[0].get("message") or {}).get("content") or "")
                result["mode"] = "chat"
                result["response_preview"] = str(content)[:120]
            result["healthy"] = True
        except httpx.HTTPStatusError as exc:
            result["error"] = f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"
        except Exception as exc:
            result["error"] = str(exc)[:300]
        result["response_time_ms"] = round((time.perf_counter() - started) * 1000, 2)
        return result


async def run(args: argparse.Namespace) -> int:
    base_url = args.base_url.rstrip("/")
    api_key = resolve_api_key(args)
    headers = build_headers(api_key, args.auth_header)
    selected_models = set(args.models or [])
    semaphore = asyncio.Semaphore(max(1, args.max_concurrency))

    async with httpx.AsyncClient(timeout=args.timeout) as client:
        models = load_models_from_yaml(args.config) if args.config else await fetch_models(client, base_url, headers)
        if selected_models:
            models = [model for model in models if model["id"] in selected_models]
        if not models:
            print("No models found to health check", file=sys.stderr)
            return 2
        results = await asyncio.gather(
            *[
                check_model(
                    client,
                    base_url,
                    headers,
                    model,
                    args.chat_prompt,
                    args.embedding_text,
                    semaphore,
                )
                for model in models
            ]
        )

    unhealthy = [result for result in results if not result.get("healthy")]
    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        for result in results:
            status = "healthy" if result.get("healthy") else "unhealthy"
            detail = result.get("response_preview") or result.get("error") or "ok"
            print(f"{result['model']}: {status} ({result.get('response_time_ms')} ms) {detail}")
        print(f"checked={len(results)} healthy={len(results) - len(unhealthy)} unhealthy={len(unhealthy)}")
    return 1 if unhealthy and args.fail_on_unhealthy else 0


def main() -> None:
    raise SystemExit(asyncio.run(run(parse_args())))


if __name__ == "__main__":
    main()
