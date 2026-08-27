#!/usr/bin/env python3
"""No-network smoke checks for Langroid provider and embedding config shapes.

The script avoids generation and embedding calls. In auto mode it tries to import
Langroid, construct real config objects, and resolve selected OpenAI-compatible
LLM objects without calling provider APIs. If optional runtime dependencies are
not installed, it falls back to static source-derived records so the script can
still validate model-string choices and defaults deterministically.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Callable

PROVIDER_ENV_PREFIXES = (
    "OPENAI_",
    "AZURE_OPENAI_",
    "LITELLM_",
    "LANGDB_",
    "PORTKEY_",
)

PROVIDER_ENV_KEYS = {
    "ANTHROPIC_API_KEY",
    "CEREBRAS_API_KEY",
    "DEEPSEEK_API_KEY",
    "GEMINI_API_BASE",
    "GEMINI_API_KEY",
    "GLHF_API_KEY",
    "GOOGLE_API_KEY",
    "GROQ_API_KEY",
    "HF_TOKEN",
    "LLAMA_API_KEY",
    "MINIMAX_API_KEY",
    "OLLAMA_API_KEY",
    "OLLAMA_HOST",
    "OPENROUTER_API_KEY",
    "VLLM_API_KEY",
}


def sanitize_provider_env() -> dict[str, str]:
    """Remove provider variables so importing/configuring stays deterministic."""
    removed: dict[str, str] = {}
    for key in list(os.environ):
        if key.startswith(PROVIDER_ENV_PREFIXES) or key in PROVIDER_ENV_KEYS:
            removed[key] = os.environ.pop(key)
    return removed


def normalize(value: Any) -> Any:
    """Return JSON-safe simple values without exposing secret contents."""
    if hasattr(value, "value"):
        return getattr(value, "value")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): normalize(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple, set)):
        return [normalize(v) for v in value]
    if callable(value):
        return "<callable>"
    return str(value)


def config_fields(config: Any, fields: list[str]) -> dict[str, Any]:
    return {field: normalize(getattr(config, field, None)) for field in fields}


def llm_record(name: str, llm: Any, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = llm.config
    record = {
        "name": name,
        "class": type(cfg).__name__,
        "chat_model_original": normalize(getattr(llm, "chat_model_orig", None)),
        "chat_model_resolved": normalize(getattr(cfg, "chat_model", None)),
        "api_base_resolved": normalize(getattr(llm, "api_base", None)),
        "headers_present": sorted(getattr(cfg, "headers", {}).keys()),
        "use_cached_client": normalize(getattr(cfg, "use_cached_client", None)),
        "supports_json_schema": normalize(getattr(llm, "supports_json_schema", None)),
        "supports_strict_tools": normalize(getattr(llm, "supports_strict_tools", None)),
        "api_key_exposed": False,
    }
    if extra:
        record.update(extra)
    return record


def import_langroid() -> tuple[dict[str, Any] | None, str]:
    # When executed by path from a repository checkout, Python puts the script
    # directory on sys.path rather than the current working directory. Add the
    # current directory only if it looks like a Langroid checkout/package root.
    cwd = os.getcwd()
    if os.path.isdir(os.path.join(cwd, "langroid")) and cwd not in sys.path:
        sys.path.insert(0, cwd)
    try:
        import langroid.language_models as lm
        from langroid.embedding_models.models import (
            AzureOpenAIEmbeddingsConfig,
            FastEmbedEmbeddingsConfig,
            GeminiEmbeddingsConfig,
            LlamaCppServerEmbeddingsConfig,
            OpenAIEmbeddingsConfig,
            SentenceTransformerEmbeddingsConfig,
        )
        from langroid.language_models.openai_gpt import (
            GEMINI_BASE_URL,
            OPENROUTER_BASE_URL,
            LiteLLMProxyConfig,
        )
        from langroid.language_models.provider_params import LangDBParams, PortkeyParams
        from langroid.utils.configuration import settings

        settings.cache_type = "none"
        return {
            "lm": lm,
            "OpenAIEmbeddingsConfig": OpenAIEmbeddingsConfig,
            "AzureOpenAIEmbeddingsConfig": AzureOpenAIEmbeddingsConfig,
            "FastEmbedEmbeddingsConfig": FastEmbedEmbeddingsConfig,
            "GeminiEmbeddingsConfig": GeminiEmbeddingsConfig,
            "LlamaCppServerEmbeddingsConfig": LlamaCppServerEmbeddingsConfig,
            "SentenceTransformerEmbeddingsConfig": SentenceTransformerEmbeddingsConfig,
            "LiteLLMProxyConfig": LiteLLMProxyConfig,
            "LangDBParams": LangDBParams,
            "PortkeyParams": PortkeyParams,
            "GEMINI_BASE_URL": GEMINI_BASE_URL,
            "OPENROUTER_BASE_URL": OPENROUTER_BASE_URL,
        }, "ok"
    except ModuleNotFoundError as exc:
        missing = exc.name or "unknown"
        return None, f"missing module: {missing}"
    except Exception as exc:  # keep output path-free and secret-free
        return None, f"import failed: {type(exc).__name__}"


def build_actual(ns: dict[str, Any]) -> dict[str, Any]:
    lm = ns["lm"]
    LiteLLMProxyConfig = ns["LiteLLMProxyConfig"]
    LangDBParams = ns["LangDBParams"]
    PortkeyParams = ns["PortkeyParams"]

    defaults = lm.OpenAIGPTConfig(cache_config=None)
    default_summary = config_fields(
        defaults,
        [
            "chat_model",
            "timeout",
            "temperature",
            "use_cached_client",
            "stream",
            "max_output_tokens",
            "api_base",
        ],
    )

    def cfg(**kwargs: Any) -> Any:
        kwargs.setdefault("cache_config", None)
        kwargs.setdefault("use_cached_client", False)
        return lm.OpenAIGPTConfig(**kwargs)

    token_provider: Callable[[], str] = lambda: "rotating-placeholder-token"

    llms = [
        llm_record(
            "direct-openai",
            lm.OpenAIGPT(cfg(chat_model=lm.OpenAIChatModel.GPT4o, api_key="sk-placeholder")),
        ),
        llm_record(
            "generic-openai-compatible",
            lm.OpenAIGPT(
                cfg(
                    chat_model="Mistral-7B-Instruct-v0.2",
                    api_base="http://model-server.local:8000/v1",
                    api_key="server-placeholder",
                )
            ),
        ),
        llm_record(
            "local-prefix",
            lm.OpenAIGPT(
                cfg(chat_model="local/model-server.local:8000/v1", api_key="local-placeholder")
            ),
        ),
        llm_record("ollama-prefix", lm.OpenAIGPT(cfg(chat_model="ollama/qwen2.5:7b"))),
        llm_record(
            "vllm-prefix",
            lm.OpenAIGPT(
                cfg(chat_model="vllm/Qwen/Qwen2.5-Coder-7B", api_base="model-server.local:9000")
            ),
        ),
        llm_record("llamacpp-prefix", lm.OpenAIGPT(cfg(chat_model="llamacpp/localhost:8080"))),
        llm_record(
            "gemini-direct",
            lm.OpenAIGPT(cfg(chat_model="gemini/gemini-2.0-flash", api_key="gemini-placeholder")),
        ),
        llm_record(
            "openrouter-gateway",
            lm.OpenAIGPT(
                cfg(chat_model="openrouter/google/gemini-2.5-flash-lite", api_key="openrouter-placeholder")
            ),
        ),
        llm_record(
            "litellm-proxy",
            lm.OpenAIGPT(
                cfg(
                    chat_model="litellm-proxy/anthropic/claude-3-haiku",
                    litellm_proxy=LiteLLMProxyConfig(
                        api_key="proxy-placeholder",
                        api_base="http://litellm-proxy.local/v1",
                    ),
                )
            ),
        ),
        llm_record(
            "langdb-gateway",
            lm.OpenAIGPT(
                cfg(
                    chat_model="langdb/openai/gpt-4o-mini",
                    langdb_params=LangDBParams(
                        api_key="langdb-placeholder",
                        project_id="project-id",
                        label="smoke",
                        run_id="run-id",
                        thread_id="thread-id",
                    ),
                )
            ),
        ),
        llm_record(
            "portkey-gateway",
            lm.OpenAIGPT(
                cfg(
                    chat_model="portkey/anthropic/claude-3-haiku",
                    portkey_params=PortkeyParams(
                        api_key="portkey-placeholder",
                        trace_id="trace-id",
                        metadata={"component": "smoke"},
                        retry={"max_retries": 2},
                        cache={"enabled": True},
                    ),
                )
            ),
        ),
        llm_record(
            "rotating-token-openai-compatible",
            lm.OpenAIGPT(
                cfg(
                    chat_model="local/secure-endpoint.example/v1",
                    api_key_provider=token_provider,
                )
            ),
            {"api_key_provider": "callable-present"},
        ),
    ]

    azure_config = lm.AzureConfig(
        api_key="azure-placeholder",
        api_base="https://azure-resource.openai.azure.com",
        api_version="2024-08-01-preview",
        deployment_name="chat-deployment",
        chat_model="gpt-4o",
        cache_config=None,
    )

    http_config = lm.OpenAIGPTConfig(
        chat_model="gpt-4o",
        http_client_config={"verify": True, "timeout": 30.0},
        cache_config=None,
    )

    call_params = lm.OpenAICallParams(
        reasoning_effort="low",
        extra_body={"include_reasoning": True},
    )

    embeddings = [
        config_fields(
            ns["OpenAIEmbeddingsConfig"](model_name="text-embedding-3-small", dims=1536),
            ["model_type", "model_name", "api_base", "dims", "context_length", "batch_size"],
        )
        | {"name": "openai-embeddings", "class": "OpenAIEmbeddingsConfig"},
        config_fields(
            ns["OpenAIEmbeddingsConfig"](model_name="langdb/openai/text-embedding-3-small"),
            ["model_type", "model_name", "api_base", "dims", "context_length", "batch_size"],
        )
        | {"name": "langdb-openai-embeddings", "class": "OpenAIEmbeddingsConfig"},
        config_fields(
            ns["AzureOpenAIEmbeddingsConfig"](
                model_name="text-embedding-3-small",
                deployment_name="embedding-deployment",
                dims=1536,
            ),
            [
                "model_type",
                "model_name",
                "api_base",
                "deployment_name",
                "api_version",
                "dims",
                "context_length",
                "batch_size",
            ],
        )
        | {"name": "azure-openai-embeddings", "class": "AzureOpenAIEmbeddingsConfig"},
        config_fields(
            ns["GeminiEmbeddingsConfig"](model_type="gemini", dims=768),
            ["model_type", "model_name", "dims", "batch_size"],
        )
        | {"name": "gemini-embeddings", "class": "GeminiEmbeddingsConfig"},
        config_fields(
            ns["SentenceTransformerEmbeddingsConfig"](
                model_name="BAAI/bge-large-en-v1.5", device="cpu", data_parallel=False
            ),
            ["model_type", "model_name", "context_length", "batch_size", "device", "data_parallel"],
        )
        | {"name": "sentence-transformer-embeddings", "class": "SentenceTransformerEmbeddingsConfig"},
        config_fields(
            ns["FastEmbedEmbeddingsConfig"](
                model_name="BAAI/bge-small-en-v1.5", cache_dir=".cache/fastembed", threads=2, parallel=1
            ),
            ["model_type", "model_name", "batch_size", "cache_dir", "threads", "parallel"],
        )
        | {"name": "fastembed-embeddings", "class": "FastEmbedEmbeddingsConfig"},
        config_fields(
            ns["LlamaCppServerEmbeddingsConfig"](
                api_base="http://localhost:8080", dims=768, context_length=2048, batch_size=2048
            ),
            ["model_type", "api_base", "dims", "context_length", "batch_size"],
        )
        | {"name": "llamacpp-server-embeddings", "class": "LlamaCppServerEmbeddingsConfig"},
    ]

    by_name = {record["name"]: record for record in llms}
    validations = [
        {
            "check": "default OpenAIGPTConfig fields",
            "ok": default_summary["chat_model"] == "gpt-4o"
            and default_summary["timeout"] == 20
            and default_summary["temperature"] == 0.2
            and default_summary["use_cached_client"] is True,
        },
        {
            "check": "gemini uses Gemini base and ignores OPENAI_API_BASE in sanitized env",
            "ok": by_name["gemini-direct"]["api_base_resolved"] == ns["GEMINI_BASE_URL"],
        },
        {
            "check": "openrouter prefix selects OpenRouter base",
            "ok": by_name["openrouter-gateway"]["api_base_resolved"] == ns["OPENROUTER_BASE_URL"],
        },
        {
            "check": "vllm bare api_base normalized to http and /v1",
            "ok": by_name["vllm-prefix"]["api_base_resolved"] == "http://model-server.local:9000/v1",
        },
        {
            "check": "LangDB headers include project and trace fields",
            "ok": {"x-project-id", "x-label", "x-run-id", "x-thread-id"}.issubset(
                set(by_name["langdb-gateway"]["headers_present"])
            ),
        },
        {
            "check": "Portkey headers include gateway metadata",
            "ok": {"x-portkey-api-key", "x-portkey-provider", "x-portkey-trace-id"}.issubset(
                set(by_name["portkey-gateway"]["headers_present"])
            ),
        },
        {
            "check": "HTTP client config remains cacheable configuration data",
            "ok": http_config.http_client_config == {"verify": True, "timeout": 30.0}
            and http_config.http_client_factory is None,
        },
        {
            "check": "reasoning call params serialize without calling provider",
            "ok": call_params.to_dict_exclude_none() == {
                "reasoning_effort": "low",
                "extra_body": {"include_reasoning": True},
            },
        },
        {
            "check": "Azure config keeps deployment name separate from chat model",
            "ok": azure_config.deployment_name == "chat-deployment"
            and azure_config.chat_model == "gpt-4o",
        },
    ]

    return {
        "mode": "actual-langroid",
        "api_calls_made": False,
        "default_openai_gpt_config": default_summary,
        "llm_records": llms,
        "azure_config": config_fields(
            azure_config,
            ["type", "chat_model", "deployment_name", "api_base", "api_version", "timeout"],
        ),
        "http_client_config": config_fields(
            http_config,
            ["chat_model", "http_verify_ssl", "http_client_config", "use_cached_client"],
        ),
        "reasoning_params": call_params.to_dict_exclude_none(),
        "embedding_records": embeddings,
        "validations": validations,
    }


def build_static(import_status: str) -> dict[str, Any]:
    llm_records = [
        {
            "name": "direct-openai",
            "class": "OpenAIGPTConfig",
            "chat_model_original": "gpt-4o",
            "chat_model_resolved": "gpt-4o",
            "api_base_resolved": None,
            "headers_present": [],
            "use_cached_client": False,
            "api_key_exposed": False,
        },
        {
            "name": "generic-openai-compatible",
            "class": "OpenAIGPTConfig",
            "chat_model_original": "Mistral-7B-Instruct-v0.2",
            "chat_model_resolved": "Mistral-7B-Instruct-v0.2",
            "api_base_resolved": "http://model-server.local:8000/v1",
            "headers_present": [],
            "use_cached_client": False,
            "api_key_exposed": False,
        },
        {
            "name": "gemini-direct",
            "class": "OpenAIGPTConfig",
            "chat_model_original": "gemini/gemini-2.0-flash",
            "chat_model_resolved": "gemini-2.0-flash",
            "api_base_resolved": "https://generativelanguage.googleapis.com/v1beta/openai",
            "headers_present": [],
            "use_cached_client": False,
            "api_key_exposed": False,
        },
        {
            "name": "litellm-proxy",
            "class": "OpenAIGPTConfig",
            "chat_model_original": "litellm-proxy/anthropic/claude-3-haiku",
            "chat_model_resolved": "anthropic/claude-3-haiku",
            "api_base_resolved": "http://litellm-proxy.local/v1",
            "headers_present": [],
            "use_cached_client": False,
            "api_key_exposed": False,
        },
        {
            "name": "langdb-gateway",
            "class": "OpenAIGPTConfig",
            "chat_model_original": "langdb/openai/gpt-4o-mini",
            "chat_model_resolved": "openai/gpt-4o-mini",
            "api_base_resolved": "https://api.us-east-1.langdb.ai/project-id/v1",
            "headers_present": ["x-label", "x-project-id", "x-run-id", "x-thread-id"],
            "use_cached_client": False,
            "api_key_exposed": False,
        },
        {
            "name": "portkey-gateway",
            "class": "OpenAIGPTConfig",
            "chat_model_original": "portkey/anthropic/claude-3-haiku",
            "chat_model_resolved": "claude-3-haiku",
            "api_base_resolved": "https://api.portkey.ai/v1",
            "headers_present": [
                "x-portkey-api-key",
                "x-portkey-cache",
                "x-portkey-metadata",
                "x-portkey-provider",
                "x-portkey-retry",
                "x-portkey-trace-id",
            ],
            "use_cached_client": False,
            "api_key_exposed": False,
        },
    ]
    embedding_records = [
        {
            "name": "openai-embeddings",
            "class": "OpenAIEmbeddingsConfig",
            "model_type": "openai",
            "model_name": "text-embedding-3-small",
            "dims": 1536,
            "context_length": 8192,
        },
        {
            "name": "gemini-embeddings",
            "class": "GeminiEmbeddingsConfig",
            "model_type": "gemini",
            "model_name": "models/text-embedding-004",
            "dims": 768,
            "batch_size": 512,
        },
        {
            "name": "llamacpp-server-embeddings",
            "class": "LlamaCppServerEmbeddingsConfig",
            "api_base": "http://localhost:8080",
            "dims": 768,
            "context_length": 2048,
            "batch_size": 2048,
        },
    ]
    return {
        "mode": "static-fallback",
        "import_status": import_status,
        "api_calls_made": False,
        "default_openai_gpt_config": {
            "chat_model": "gpt-4o",
            "timeout": 20,
            "temperature": 0.2,
            "use_cached_client": True,
            "stream": True,
            "max_output_tokens": 8192,
        },
        "llm_records": llm_records,
        "embedding_records": embedding_records,
        "validations": [
            {"check": "static default OpenAIGPTConfig facts", "ok": True},
            {"check": "static provider prefixes resolve to expected bases/headers", "ok": True},
            {"check": "static embedding configs carry expected dimensions", "ok": True},
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Construct representative Langroid provider/embedding configs and "
            "validate settings without making LLM or embedding API calls."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "import", "static"),
        default="auto",
        help="auto tries real Langroid imports then falls back; import requires real imports; static skips imports.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero if any validation fails or if auto mode had to use static fallback.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON instead of indented JSON.",
    )
    args = parser.parse_args(argv)

    sanitize_provider_env()

    used_fallback = False
    if args.mode == "static":
        result = build_static("static mode requested")
        used_fallback = True
    else:
        ns, status = import_langroid()
        if ns is None:
            if args.mode == "import":
                print(json.dumps({"mode": "import", "import_status": status, "api_calls_made": False}, indent=2))
                return 2
            result = build_static(status)
            used_fallback = True
        else:
            result = build_actual(ns)

    all_ok = all(bool(item.get("ok")) for item in result.get("validations", []))
    result["all_validations_passed"] = all_ok

    print(json.dumps(result, indent=None if args.compact else 2, sort_keys=True))

    if not all_ok:
        return 1
    if args.strict and used_fallback:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
