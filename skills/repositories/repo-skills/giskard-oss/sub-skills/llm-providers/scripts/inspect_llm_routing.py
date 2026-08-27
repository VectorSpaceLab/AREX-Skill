#!/usr/bin/env python3
"""Deterministic no-provider inspection for giskard.llm routing.

The script prints a JSON summary of public signatures, provider-prefix routing,
alias resolution behavior, response-model behavior, retry classification, and
next steps when provider SDKs are missing. It does not make network calls or
invoke any live provider SDK methods.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import os
import sys
from dataclasses import asdict, dataclass
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch


def _disable_telemetry() -> None:
    os.environ.setdefault("DO_NOT_TRACK", "1")
    os.environ.setdefault("GISKARD_TELEMETRY_DISABLED", "1")


def _safe_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "<unavailable>"


def _redact_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in kwargs.items():
        if key == "api_key":
            redacted[key] = "<resolved>" if value else None
        elif key == "http_client":
            redacted[key] = "<caller-owned-client>"
        else:
            redacted[key] = value
    return redacted


def _summarize_error(error: Exception, should_retry: Any) -> dict[str, Any]:
    return {
        "type": type(error).__name__,
        "status_code": getattr(error, "status_code", None),
        "provider": getattr(error, "provider", None),
        "retry": should_retry(error),
    }


def _next_steps_from_availability(sdk_availability: dict[str, bool]) -> list[str]:
    steps: list[str] = []
    if not sdk_availability.get("openai", False):
        steps.append(
            "Install giskard-llm[openai] to cover OpenAI, Azure OpenAI, and Azure AI Foundry."
        )
    if not sdk_availability.get("google.genai", False):
        steps.append("Install giskard-llm[google] for Google Gemini support.")
    if not sdk_availability.get("anthropic", False):
        steps.append("Install giskard-llm[anthropic] for Anthropic support.")
    if not steps:
        steps.append(
            "All known provider SDKs are importable; continue with alias and credential checks."
        )
    return steps


def main() -> int:
    _disable_telemetry()

    sdk_availability = {
        "openai": importlib.util.find_spec("openai") is not None,
        "google.genai": importlib.util.find_spec("google.genai") is not None,
        "anthropic": importlib.util.find_spec("anthropic") is not None,
    }

    try:
        import giskard.llm as llm
        from giskard.llm import errors as llm_errors
        from giskard.llm import routing
        from giskard.llm.chat import assistant, developer, message, system, user
        from giskard.llm.providers.anthropic import AnthropicProvider
        from giskard.llm.providers.azure_ai import AzureAIProvider
        from giskard.llm.providers.azure_openai import AzureOpenAIProvider
        from giskard.llm.providers.google import GoogleProvider
        from giskard.llm.providers.openai import OpenAIProvider
        from giskard.llm.types import (
            AssistantMessage,
            Choice,
            CompletionResponse,
            EmbeddingData,
            EmbeddingResponse,
            EmbeddingUsage,
            FunctionCallOutput,
            ResponseFunctionToolCall,
            ResponseOutputMessage,
            ResponseOutputText,
            ResponseResult,
            ToolCall,
            ToolCallFunction,
            Usage,
        )
    except Exception as exc:  # pragma: no cover - deterministic error path
        payload = {
            "ok": False,
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
            "sdk_availability": sdk_availability,
            "next_steps": [
                "Install or expose the giskard package first, then rerun the inspector.",
                *_next_steps_from_availability(sdk_availability),
            ],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2

    package_version = getattr(llm, "__version__", None)

    provider_classes = {
        "openai": OpenAIProvider,
        "google": GoogleProvider,
        "gemini": GoogleProvider,
        "anthropic": AnthropicProvider,
        "azure": AzureOpenAIProvider,
        "azure_ai": AzureAIProvider,
    }

    signatures = {
        "LLMClient": _safe_signature(llm.LLMClient),
        "LLMClient.configure": _safe_signature(llm.LLMClient.configure),
        "LLMClient.configure_from_dict": _safe_signature(
            llm.LLMClient.configure_from_dict
        ),
        "LLMClient.acompletion": _safe_signature(llm.LLMClient.acompletion),
        "LLMClient.aembedding": _safe_signature(llm.LLMClient.aembedding),
        "LLMClient.aresponse": _safe_signature(llm.LLMClient.aresponse),
        "configure": _safe_signature(llm.configure),
        "reset": _safe_signature(llm.reset),
        "acompletion": _safe_signature(llm.acompletion),
        "aembedding": _safe_signature(llm.aembedding),
        "aresponse": _safe_signature(llm.aresponse),
        "should_retry": _safe_signature(llm.should_retry),
        "error:LLMError": _safe_signature(llm_errors.LLMError),
        "error:ProviderNotAvailableError": _safe_signature(
            llm_errors.ProviderNotAvailableError
        ),
    }

    model_parsing = {
        "registry": sorted(routing._PROVIDER_REGISTRY),
        "examples": {},
        "bare_default": routing._parse_model_string("gpt-4o"),
        "env_resolution": {
            "string": routing._resolve_value("os.environ/GISKARD_LLM_INSPECT_KEY"),
            "non_string": routing._resolve_value(42),
        },
    }
    for sample in [
        "openai/gpt-4o",
        "google/gemini-2.0-flash",
        "gemini/gemini-2.0-flash",
        "anthropic/claude-3-5-sonnet-latest",
        "azure/gpt-4o",
        "azure_ai/gpt-4o",
    ]:
        model_parsing["examples"][sample] = routing._parse_model_string(sample)

    provider_capabilities = {
        name: {
            "complete": hasattr(cls, "complete"),
            "embed": hasattr(cls, "embed"),
            "respond": hasattr(cls, "respond"),
        }
        for name, cls in provider_classes.items()
    }

    # Alias configuration behavior: resolve env refs and keep cached provider objects.
    os.environ["GISKARD_LLM_INSPECT_KEY"] = "resolved"
    os.environ["GISKARD_LLM_INSPECT_OPENAI_KEY"] = "openai-key-present"
    os.environ["GISKARD_LLM_INSPECT_GOOGLE_KEY"] = "google-key-present"
    os.environ["GISKARD_LLM_INSPECT_ANTHROPIC_KEY"] = "anthropic-key-present"

    created: list[dict[str, Any]] = []

    def fake_create(provider_type: str, **kwargs: Any) -> SimpleNamespace:
        created.append({"provider": provider_type, "kwargs": _redact_kwargs(kwargs)})
        return SimpleNamespace(provider_type=provider_type, kwargs=kwargs)

    client = llm.LLMClient()
    client.configure(
        "openai-prod",
        provider="openai",
        api_key="os.environ/GISKARD_LLM_INSPECT_OPENAI_KEY",
        base_url="https://example.invalid/openai/v1/",
    )
    client.configure(
        "google-prod",
        provider="google",
        api_key="os.environ/GISKARD_LLM_INSPECT_GOOGLE_KEY",
    )
    client.configure(
        "anthropic-relaxed",
        provider="anthropic",
        api_key="os.environ/GISKARD_LLM_INSPECT_ANTHROPIC_KEY",
        merge_system=True,
    )

    with patch.object(routing, "_create_provider", side_effect=fake_create):
        first = client._get_provider("openai-prod")
        second = client._get_provider("openai-prod")
        google = client._get_provider("google-prod")
        anthropic = client._get_provider("anthropic-relaxed")

    alias_resolution = {
        "cached_identity": first is second,
        "provider_records": created,
        "google_provider_type": getattr(google, "provider_type", None),
        "anthropic_provider_type": getattr(anthropic, "provider_type", None),
    }

    response_models = {
        "assistant_message_dump": AssistantMessage(content="Hello").model_dump(),
        "tool_call_arguments_from_json": ToolCallFunction(
            name="add", arguments='{"a": 1, "b": 2}'
        ).arguments,
        "completion_response": CompletionResponse(
            choices=[
                Choice(
                    message=AssistantMessage(content="Hello"),
                    finish_reason="stop",
                )
            ],
            model="gpt-4o",
            usage=Usage(input_tokens=3, output_tokens=2, total_tokens=5),
        ).model_dump(),
        "embedding_response": EmbeddingResponse(
            data=[EmbeddingData(embedding=[0.1, 0.2], index=0)],
            model="text-embedding-3-small",
            usage=EmbeddingUsage(prompt_tokens=2, total_tokens=2),
        ).model_dump(),
        "response_result": ResponseResult(
            id="resp_1",
            outputs=[
                ResponseOutputMessage(
                    role="assistant",
                    content=[ResponseOutputText(text="Done")],
                ),
                ResponseFunctionToolCall(
                    call_id="call_1", name="add", arguments={"a": 1}
                ),
            ],
            model="gpt-4o",
        ).model_dump(),
        "function_call_output_dump": FunctionCallOutput(
            call_id="call_1", name="add", output="7"
        ).model_dump(),
        "helpers": {
            "system": system("Be concise.").model_dump(),
            "developer": developer("Use bullets.").model_dump(),
            "user": user("Hello").model_dump(),
            "assistant": assistant("Hi").model_dump(),
            "message(user)": message("Hello", "user").model_dump(),
        },
    }

    retry_matrix = {
        "timeout": _summarize_error(
            llm_errors.LLMTimeoutError(408, "timeout", "openai"), llm.should_retry
        ),
        "rate_limit": _summarize_error(
            llm_errors.RateLimitError(429, "rate limited", "openai"), llm.should_retry
        ),
        "server": _summarize_error(
            llm_errors.ServerError(503, "server error", "openai"), llm.should_retry
        ),
        "auth": _summarize_error(
            llm_errors.AuthenticationError(401, "auth", "openai"), llm.should_retry
        ),
        "bad_request": _summarize_error(
            llm_errors.BadRequestError(400, "bad request", "openai"), llm.should_retry
        ),
        "generic": _summarize_error(
            llm_errors.LLMError(500, "generic", "openai"), llm.should_retry
        ),
    }

    output = {
        "ok": True,
        "package_version": package_version,
        "python": sys.version.split()[0],
        "sdk_availability": sdk_availability,
        "signatures": signatures,
        "model_parsing": model_parsing,
        "provider_capabilities": provider_capabilities,
        "alias_resolution": alias_resolution,
        "response_models": response_models,
        "retry_matrix": retry_matrix,
        "next_steps": _next_steps_from_availability(sdk_availability),
    }

    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
