#!/usr/bin/env python3
"""Validate dispatcher provider metadata without credentials or network access.

This helper intentionally accepts only non-secret configuration metadata. It
mirrors domestic preset normalization and prints a JSON summary; it never
imports provider SDKs, reads environment values, contacts an endpoint, or
starts a subprocess.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

SUPPORTED_PROVIDERS = ("anthropic", "openai", "claude_cli", "codex_cli")
PROVIDER_PRESETS = {
    "deepseek": ("https://api.deepseek.com/v1", "DEEPSEEK_API_KEY"),
    "dashscope": (
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "DASHSCOPE_API_KEY",
    ),
    "qwen": (
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "DASHSCOPE_API_KEY",
    ),
    "moonshot": ("https://api.moonshot.cn/v1", "MOONSHOT_API_KEY"),
    "kimi": ("https://api.moonshot.cn/v1", "MOONSHOT_API_KEY"),
    "zhipu": ("https://open.bigmodel.cn/api/paas/v4", "ZHIPUAI_API_KEY"),
    "glm": ("https://open.bigmodel.cn/api/paas/v4", "ZHIPUAI_API_KEY"),
}


def normalize(
    provider: str,
    model: str,
    base_url: Optional[str],
    api_key_env: Optional[str],
    auth_token_env: Optional[str],
) -> dict:
    """Return non-secret dispatcher metadata using source-compatible rules."""
    label = provider
    preset = PROVIDER_PRESETS.get(provider)
    if preset:
        preset_url, preset_key_env = preset
        base_url = (base_url or "").strip() or preset_url
        api_key_env = (api_key_env or "").strip() or preset_key_env
        provider = "openai"

    if provider not in SUPPORTED_PROVIDERS:
        options = ", ".join(SUPPORTED_PROVIDERS + tuple(PROVIDER_PRESETS))
        raise ValueError(f"Unknown provider '{provider}'. Use one of: {options}")

    return {
        "provider_label": label,
        "provider": provider,
        "model": model,
        "base_url": (base_url or "").strip() or None,
        "api_key_env": (api_key_env or "").strip() or None,
        "auth_token_env": (auth_token_env or "").strip() or None,
        "secret_values_read": False,
        "network_access": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate provider metadata without reading secrets or using the network."
    )
    parser.add_argument("--provider", default="anthropic")
    parser.add_argument("--model", default="claude-sonnet-4-6")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--api-key-env", default="")
    parser.add_argument("--auth-token-env", default="")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = normalize(
            provider=args.provider,
            model=args.model,
            base_url=args.base_url,
            api_key_env=args.api_key_env,
            auth_token_env=args.auth_token_env,
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
