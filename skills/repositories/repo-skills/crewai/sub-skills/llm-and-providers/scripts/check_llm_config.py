#!/usr/bin/env python3
"""Offline CrewAI LLM configuration checker.

This script inspects model/provider/base-url choices and reports which
environment variables or placeholder credentials would be needed. It does not
import CrewAI, call provider SDKs, read secret values, make network requests, or
execute LLM calls.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from urllib.parse import urlparse


NATIVE_PROVIDERS = {
    "openai",
    "anthropic",
    "claude",
    "azure",
    "azure_openai",
    "google",
    "gemini",
    "bedrock",
    "aws",
    "snowflake",
}

OPENAI_COMPATIBLE = {
    "openrouter": {
        "api_key_env": "OPENROUTER_API_KEY",
        "base_url_env": "OPENROUTER_BASE_URL",
        "default_base_url": "https://openrouter.ai/api/v1",
        "api_key_required": True,
        "default_api_key": None,
    },
    "deepseek": {
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url_env": "DEEPSEEK_BASE_URL",
        "default_base_url": "https://api.deepseek.com/v1",
        "api_key_required": True,
        "default_api_key": None,
    },
    "ollama": {
        "api_key_env": "OLLAMA_API_KEY",
        "base_url_env": "OLLAMA_HOST",
        "default_base_url": "http://localhost:11434/v1",
        "api_key_required": False,
        "default_api_key": "ollama",
    },
    "ollama_chat": {
        "api_key_env": "OLLAMA_API_KEY",
        "base_url_env": "OLLAMA_HOST",
        "default_base_url": "http://localhost:11434/v1",
        "api_key_required": False,
        "default_api_key": "ollama",
    },
    "hosted_vllm": {
        "api_key_env": "VLLM_API_KEY",
        "base_url_env": "VLLM_BASE_URL",
        "default_base_url": "http://localhost:8000/v1",
        "api_key_required": False,
        "default_api_key": "dummy",
    },
    "cerebras": {
        "api_key_env": "CEREBRAS_API_KEY",
        "base_url_env": "CEREBRAS_BASE_URL",
        "default_base_url": "https://api.cerebras.ai/v1",
        "api_key_required": True,
        "default_api_key": None,
    },
    "dashscope": {
        "api_key_env": "DASHSCOPE_API_KEY",
        "base_url_env": "DASHSCOPE_BASE_URL",
        "default_base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "api_key_required": True,
        "default_api_key": None,
    },
}

OPENAI_MODEL_PREFIXES = ("gpt-", "o1", "o3", "o4", "whisper-")
ANTHROPIC_MODEL_PREFIXES = ("claude-", "anthropic.")
GEMINI_MODEL_PREFIXES = ("gemini-", "gemma-", "learnlm-")
AZURE_MODEL_PREFIXES = ("gpt-", "gpt-35-", "o1", "o3", "o4", "azure-")
SNOWFLAKE_CORTEX_PATH = "/api/v2/cortex/v1"


@dataclass(frozen=True)
class CheckResult:
    provider: str
    model_name: str
    route: str
    env_vars: list[str]
    warnings: list[str]
    suggestions: list[str]


def env_status(name: str) -> str:
    return "set" if os.getenv(name) else "missing"


def split_model(model: str) -> tuple[str | None, str]:
    if "/" not in model:
        return None, model
    provider, _, model_name = model.partition("/")
    return provider.lower(), model_name


def infer_provider(model_name: str) -> str:
    lowered = model_name.lower()
    if lowered.startswith(ANTHROPIC_MODEL_PREFIXES):
        return "anthropic"
    if lowered.startswith(GEMINI_MODEL_PREFIXES):
        return "gemini"
    if "." in lowered and any(
        token in lowered for token in ("anthropic", "amazon", "meta", "mistral", "ai21")
    ):
        return "bedrock"
    if lowered.startswith(OPENAI_MODEL_PREFIXES):
        return "openai"
    return "openai"


def canonical_provider(provider: str) -> str:
    mapping = {
        "claude": "anthropic",
        "google": "gemini",
        "aws": "bedrock",
        "azure_openai": "azure",
    }
    return mapping.get(provider.lower(), provider.lower())


def normalize_ollama_url(value: str) -> str:
    stripped = value.rstrip("/")
    if not stripped.endswith("/v1"):
        return f"{stripped}/v1"
    return stripped


def describe_url(url: str | None, provider: str) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    if not url:
        return None, warnings

    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        warnings.append("base_url does not look like an absolute URL")

    path = (parsed.path or "").rstrip("/")
    if provider in {"openai", "ollama", "ollama_chat", "hosted_vllm", "deepseek", "openrouter", "cerebras", "dashscope"}:
        if path.endswith("/chat/completions"):
            warnings.append("OpenAI-compatible base_url should normally be the API root, not /chat/completions")
        elif path and not path.endswith("/v1") and provider != "snowflake":
            warnings.append("OpenAI-compatible base_url usually ends with /v1")
    if provider == "snowflake" and "/chat/completions" in path:
        warnings.append("Snowflake base URL should be account URL or Cortex root, not /chat/completions")
    return parsed.netloc + (parsed.path or ""), warnings


def required_for_provider(provider: str) -> tuple[list[str], list[str], str | None]:
    provider = canonical_provider(provider)
    if provider == "openai":
        return ["OPENAI_API_KEY"], ["OPENAI_BASE_URL", "OPENAI_API_BASE", "BASE_URL"], None
    if provider == "anthropic":
        return ["ANTHROPIC_API_KEY"], [], None
    if provider == "gemini":
        return ["GOOGLE_API_KEY or GEMINI_API_KEY"], ["GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION", "GOOGLE_GENAI_USE_VERTEXAI"], None
    if provider == "azure":
        return ["AZURE_API_KEY", "AZURE_ENDPOINT or AZURE_OPENAI_ENDPOINT or AZURE_API_BASE"], ["AZURE_API_VERSION", "AZURE_CREDENTIAL_SCOPES"], "2024-06-01 default api_version"
    if provider == "bedrock":
        return ["AWS credentials", "AWS_DEFAULT_REGION or AWS_REGION_NAME"], ["AWS_SESSION_TOKEN"], None
    if provider == "snowflake":
        return ["SNOWFLAKE_PAT or SNOWFLAKE_TOKEN or SNOWFLAKE_JWT", "SNOWFLAKE_ACCOUNT_URL or SNOWFLAKE_ACCOUNT"], ["SNOWFLAKE_ACCOUNT_ID", "SNOWFLAKE_ACCOUNT_IDENTIFIER"], None
    if provider in OPENAI_COMPATIBLE:
        config = OPENAI_COMPATIBLE[provider]
        required = []
        note = None
        if config["api_key_required"]:
            required.append(str(config["api_key_env"]))
        else:
            note = f"uses placeholder api_key={config['default_api_key']!r} if no key is set"
        optional = [str(config["base_url_env"])] if config["base_url_env"] else []
        return required, optional, note
    return [], [], None


def check_config(model: str, explicit_provider: str | None, base_url: str | None) -> CheckResult:
    prefix, model_name = split_model(model)
    provider = canonical_provider(explicit_provider or prefix or infer_provider(model_name))
    warnings: list[str] = []
    suggestions: list[str] = []

    if explicit_provider and prefix and canonical_provider(prefix) != provider:
        warnings.append(
            f"explicit provider {explicit_provider!r} differs from model prefix {prefix!r}; CrewAI prioritizes explicit provider"
        )

    if provider in OPENAI_COMPATIBLE:
        route = "native OpenAI-compatible provider"
        config = OPENAI_COMPATIBLE[provider]
        if not base_url:
            env_url = os.getenv(str(config["base_url_env"])) if config["base_url_env"] else None
            base_url = env_url or str(config["default_base_url"])
        if provider in {"ollama", "ollama_chat"} and base_url:
            normalized = normalize_ollama_url(base_url)
            if normalized != base_url:
                suggestions.append(f"Ollama URL will be normalized to {normalized}")
                base_url = normalized
    elif provider in NATIVE_PROVIDERS:
        route = "native provider"
    else:
        route = "LiteLLM fallback"
        suggestions.append("Install crewai[litellm] intentionally or switch to a native provider prefix")

    if not explicit_provider and not prefix and provider == "openai" and not model_name.lower().startswith(OPENAI_MODEL_PREFIXES):
        warnings.append("unknown unprefixed model will likely route as OpenAI; add an explicit provider if this is not intended")

    if provider == "azure" and not (model_name.lower().startswith(AZURE_MODEL_PREFIXES) or explicit_provider):
        suggestions.append("Azure model names usually refer to deployment names; verify the deployment exists")

    if provider == "snowflake" and base_url and base_url.rstrip("/").endswith(SNOWFLAKE_CORTEX_PATH):
        suggestions.append("Snowflake Cortex root is acceptable; do not append /chat/completions")

    _, url_warnings = describe_url(base_url, provider)
    warnings.extend(url_warnings)

    required, optional, note = required_for_provider(provider)
    env_vars = required + optional
    if note:
        suggestions.append(note)

    return CheckResult(
        provider=provider,
        model_name=model_name,
        route=route,
        env_vars=env_vars,
        warnings=warnings,
        suggestions=suggestions,
    )


def print_report(result: CheckResult) -> None:
    print("CrewAI LLM offline configuration check")
    print(f"Provider: {result.provider}")
    print(f"Model name passed to provider: {result.model_name}")
    print(f"Route: {result.route}")

    if result.env_vars:
        print("\nCredential/config environment variables:")
        for name in result.env_vars:
            if " or " in name:
                parts = [part.strip() for part in name.split(" or ")]
                statuses = ", ".join(f"{part}={env_status(part)}" for part in parts)
                print(f"- {name}: {statuses}")
            else:
                print(f"- {name}: {env_status(name)}")
    else:
        print("\nCredential/config environment variables: none known for this route")

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"- {warning}")

    if result.suggestions:
        print("\nSuggestions:")
        for suggestion in result.suggestions:
            print(f"- {suggestion}")

    print("\nNo network calls were made and no secret values were printed.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check CrewAI LLM model/provider/base-url configuration without network calls.",
    )
    parser.add_argument("--model", required=True, help="CrewAI LLM model string, e.g. openai/gpt-4o-mini or ollama/llama3")
    parser.add_argument("--provider", help="Explicit provider argument that would be passed to LLM(provider=...)")
    parser.add_argument("--base-url", help="Explicit base_url/api_base value to inspect")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = check_config(args.model, args.provider, args.base_url)
    print_report(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
