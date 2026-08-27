#!/usr/bin/env python3
"""Secret-safe import and environment checker for Unstructured embedding providers.

This helper intentionally does not instantiate provider clients or call embedding APIs.
It reports whether provider modules/classes import and whether common credential
environment variables are present, without printing secret values.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderCheck:
    key: str
    module: str
    config_class: str
    encoder_class: str
    sdk_modules: tuple[str, ...]
    env_vars: tuple[str, ...]
    notes: str


PROVIDERS: dict[str, ProviderCheck] = {
    "openai": ProviderCheck(
        key="openai",
        module="unstructured.embed.openai",
        config_class="OpenAIEmbeddingConfig",
        encoder_class="OpenAIEmbeddingEncoder",
        sdk_modules=("langchain_openai",),
        env_vars=("OPENAI_API_KEY",),
        notes="LangChain OpenAI route; config requires an API key and model name defaults in code.",
    ),
    "octoai": ProviderCheck(
        key="octoai",
        module="unstructured.embed.octoai",
        config_class="OctoAiEmbeddingConfig",
        encoder_class="OctoAIEmbeddingEncoder",
        sdk_modules=("openai", "tiktoken"),
        env_vars=("OCTOAI_API_KEY",),
        notes="Uses the OpenAI SDK with the OctoAI base URL; large document sets may need external batching.",
    ),
    "mixedbread-ai": ProviderCheck(
        key="mixedbread-ai",
        module="unstructured.embed.mixedbreadai",
        config_class="MixedbreadAIEmbeddingConfig",
        encoder_class="MixedbreadAIEmbeddingEncoder",
        sdk_modules=("mixedbread_ai",),
        env_vars=("MXBAI_API_KEY",),
        notes="Config can default from MXBAI_API_KEY; initialize() sets request timeout/retry options.",
    ),
    "voyageai": ProviderCheck(
        key="voyageai",
        module="unstructured.embed.voyageai",
        config_class="VoyageAIEmbeddingConfig",
        encoder_class="VoyageAIEmbeddingEncoder",
        sdk_modules=("voyageai",),
        env_vars=("VOYAGE_API_KEY",),
        notes="Token-aware batching and optional output_dimension; show_progress_bar also requires tqdm.",
    ),
    "vertexai": ProviderCheck(
        key="vertexai",
        module="unstructured.embed.vertexai",
        config_class="VertexAIEmbeddingConfig",
        encoder_class="VertexAIEmbeddingEncoder",
        sdk_modules=("langchain", "langchain_google_vertexai"),
        env_vars=("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_VERTEX_CREDENTIALS_JSON"),
        notes="Config expects service-account JSON; get_client() writes Google credentials, so this checker avoids it.",
    ),
    "bedrock": ProviderCheck(
        key="bedrock",
        module="unstructured.embed.bedrock",
        config_class="BedrockEmbeddingConfig",
        encoder_class="BedrockEmbeddingEncoder",
        sdk_modules=("boto3", "langchain_community"),
        env_vars=("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION", "AWS_DEFAULT_REGION"),
        notes="Config requires explicit AWS access key, secret key, and region fields in this implementation.",
    ),
    "huggingface": ProviderCheck(
        key="huggingface",
        module="unstructured.embed.huggingface",
        config_class="HuggingFaceEmbeddingConfig",
        encoder_class="HuggingFaceEmbeddingEncoder",
        sdk_modules=("langchain_huggingface",),
        env_vars=("HF_HOME", "HUGGINGFACE_HUB_CACHE", "HF_TOKEN"),
        notes="Local model route; optional installs can be heavy and may download model files.",
    ),
}

ALIASES = {
    "langchain-openai": "openai",
    "langchain-huggingface": "huggingface",
    "langchain-aws-bedrock": "bedrock",
    "langchain-vertexai": "vertexai",
    "mixedbread": "mixedbread-ai",
    "mxbai": "mixedbread-ai",
    "voyage": "voyageai",
    "vertex": "vertexai",
    "aws-bedrock": "bedrock",
    "hf": "huggingface",
}


def import_status(module_name: str) -> dict[str, Any]:
    try:
        importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - report import blocker class safely.
        return {"ok": False, "error_type": type(exc).__name__, "message": str(exc)}
    return {"ok": True}


def class_status(module_name: str, class_names: tuple[str, ...]) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        missing = [name for name in class_names if not hasattr(module, name)]
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error_type": type(exc).__name__, "message": str(exc)}
    if missing:
        return {"ok": False, "missing_classes": missing}
    return {"ok": True}


def check_provider(provider: ProviderCheck) -> dict[str, Any]:
    return {
        "provider": provider.key,
        "unstructured_module": provider.module,
        "classes": class_status(provider.module, (provider.config_class, provider.encoder_class)),
        "sdk_imports": {name: import_status(name) for name in provider.sdk_modules},
        "env_presence": {name: bool(os.environ.get(name)) for name in provider.env_vars},
        "notes": provider.notes,
    }


def resolve_provider(name: str) -> str:
    normalized = name.strip().lower()
    return ALIASES.get(normalized, normalized)


def print_text(results: list[dict[str, Any]]) -> None:
    for result in results:
        print(f"Provider: {result['provider']}")
        classes = result["classes"]
        print(f"  unstructured classes: {'ok' if classes.get('ok') else 'missing/error'}")
        if not classes.get("ok"):
            print(f"    detail: {classes}")
        print("  SDK imports:")
        for module_name, status in result["sdk_imports"].items():
            line = "ok" if status.get("ok") else f"missing/error ({status.get('error_type')})"
            print(f"    {module_name}: {line}")
        print("  environment variables present:")
        for env_name, present in result["env_presence"].items():
            print(f"    {env_name}: {'present' if present else 'absent'}")
        print(f"  note: {result['notes']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider",
        action="append",
        choices=sorted(set(PROVIDERS) | set(ALIASES)),
        help="Provider to check. May be repeated. Use --all to check every provider.",
    )
    parser.add_argument("--all", action="store_true", help="Check every known provider.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    args = parser.parse_args()

    if args.all:
        provider_keys = sorted(PROVIDERS)
    elif args.provider:
        provider_keys = [resolve_provider(name) for name in args.provider]
    else:
        parser.error("choose --provider PROVIDER or --all")

    unknown = sorted({key for key in provider_keys if key not in PROVIDERS})
    if unknown:
        parser.error(f"unknown provider(s): {', '.join(unknown)}")

    results = [check_provider(PROVIDERS[key]) for key in provider_keys]
    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print_text(results)

    failed_core_imports = [result["provider"] for result in results if not result["classes"].get("ok")]
    return 1 if failed_core_imports else 0


if __name__ == "__main__":
    raise SystemExit(main())
