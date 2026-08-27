# Model Clients

Model clients live under `autogen_ext.models.*` and implement `autogen_core.models.ChatCompletionClient`-style surfaces for AgentChat and Core code. This reference focuses on setup and diagnostics; route team construction, termination, streaming, and memory use inside agents to `agentchat-workflows`.

## Client Selection

| Provider/path | Extra | Public class | Minimal configuration decision |
| --- | --- | --- | --- |
| OpenAI hosted or OpenAI-compatible endpoint | `openai` | `autogen_ext.models.openai.OpenAIChatCompletionClient` | `model`; optionally `api_key`, `base_url`, `model_info`, `include_name_in_message` |
| Azure OpenAI | `openai` plus Azure identity only if using token provider | `autogen_ext.models.openai.AzureOpenAIChatCompletionClient` | `azure_endpoint`, `azure_deployment`, `api_version`, `model`, and either key or token provider |
| Azure AI Foundry or GitHub Models via Azure AI Inference | `azure` | `autogen_ext.models.azure.AzureAIChatCompletionClient` | `endpoint`, `credential`, `model_info`; GitHub Models also needs `model` |
| Anthropic direct | `anthropic` | `autogen_ext.models.anthropic.AnthropicChatCompletionClient` | `model`, API key, optional `model_info` overrides |
| Anthropic Bedrock | `anthropic` | `autogen_ext.models.anthropic.AnthropicBedrockChatCompletionClient` | model plus AWS Bedrock credential info/region |
| Ollama | `ollama` | `autogen_ext.models.ollama.OllamaChatCompletionClient` | `model`, optional `host`, compatible local service/model |
| llama.cpp | `llama-cpp` | `autogen_ext.models.llama_cpp.LlamaCppChatCompletionClient` | local model path and llama-cpp-python compatibility |
| Semantic Kernel connector | `semantic-kernel-core` plus provider extra | `autogen_ext.models.semantic_kernel.SKChatCompletionAdapter` | existing SK chat completion client and execution settings |
| Deterministic replay | none beyond base install | `autogen_ext.models.replay.ReplayChatCompletionClient` | replay messages/results for tests and offline flows |
| Cached model calls | model extra plus cache extra | `autogen_ext.models.cache.ChatCompletionCache` | wrapped client plus `DiskCacheStore` or `RedisStore` |

## OpenAI-Compatible Setup

Use `OpenAIChatCompletionClient` for OpenAI-hosted models and, with care, OpenAI-compatible endpoints. Known OpenAI models can infer model capabilities. Unknown/custom models require explicit `model_info`; otherwise construction raises a `ValueError` that `model_info` is required.

Safe no-call diagnostics:

```python
from autogen_ext.models.openai import OpenAIChatCompletionClient

client = OpenAIChatCompletionClient(
    model="custom-model",
    base_url="https://example.invalid/v1",
    api_key="placeholder",
    model_info={
        "vision": False,
        "function_calling": False,
        "json_output": False,
        "family": "unknown",
        "structured_output": False,
    },
)
```

This validates constructor shape only. Do not call `create()` or `create_stream()` without explicit provider credentials and network approval.

## Azure OpenAI Setup

`AzureOpenAIChatCompletionClient` requires Azure-specific routing fields:

- `azure_endpoint`: base Azure OpenAI endpoint.
- `azure_deployment`: deployment name, not necessarily the public model name.
- `api_version`: Azure OpenAI API version string.
- `model`: used for AutoGen model metadata/capability handling.
- Authentication: API key, `azure_ad_token`, or `azure_ad_token_provider`.

When using `AzureTokenProvider`, the serialized component support currently expects `DefaultAzureCredential` with scopes. The identity needs the appropriate Azure OpenAI role. Diagnose Azure OpenAI failures by separating: import/extra, endpoint shape, deployment name, API version, credential type, role assignment, and network access.

## Azure AI Inference / GitHub Models

`AzureAIChatCompletionClient` comes from the `azure` extra, not the `openai` extra. It validates `endpoint`, `credential`, and `model_info`; GitHub Models usage also requires `model`. Structured output is not currently supported for this client. Use Azure credential classes from the Azure SDK, but do not instantiate long-lived credentials or call the service during import-only checks.

## Anthropic and Bedrock

Use the direct Anthropic client for Anthropic API access and the Bedrock client when the model is served through AWS Bedrock. Check whether function calling, JSON output, and vision support are represented correctly in `model_info`. For Bedrock, distinguish Anthropic API key failures from AWS access key/session/region failures.

## Ollama and llama.cpp

Ollama and llama.cpp are local model paths but still require runtime resources:

- Ollama import success does not prove that the Ollama server is running or that the requested model has been pulled.
- llama.cpp import success does not prove that the model file exists, that the native wheel is compatible with the platform, or that GPU/CPU settings are valid.

If a user wants offline model execution, first inspect imports, then confirm service/model file availability, then run a tiny explicit model-call smoke test only when allowed.

## Semantic Kernel Adapter

`SKChatCompletionAdapter` wraps a Semantic Kernel chat completion service. Install `semantic-kernel-core` plus the provider connector extra such as `semantic-kernel-google`, `semantic-kernel-ollama`, or `semantic-kernel-anthropic`. The adapter may warn or reject features not supported by the underlying SK connector, including structured output and some `tool_choice` combinations.

## Cache Wrapping

`ChatCompletionCache` wraps a model client and a cache store. Select cache storage separately:

- `DiskCacheStore` requires `autogen-ext[diskcache]` and a writable directory.
- `RedisStore` requires `autogen-ext[redis]` and a caller-managed `redis.Redis` instance.

Redis cache `get()` returns defaults gracefully on Redis/connection errors, while `set()` suppresses Redis/serialization errors. That robustness can hide cache outages, so inspect service status when cache hits unexpectedly disappear.

## Common No-Credential Checks

- Import the public module and class.
- Instantiate only with placeholder credentials when constructor validation is the target and no provider call is made.
- Verify unknown/custom models include `model_info`.
- Verify Azure variants use the right endpoint/deployment/API version field names.
- Confirm serialized component configs do not leak secrets before logging them.
