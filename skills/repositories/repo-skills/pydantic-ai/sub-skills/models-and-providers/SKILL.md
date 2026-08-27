---
name: models-and-providers
description: "Guides agents through Pydantic AI model selection, provider
  configuration, optional extras, native tools, embeddings, wrappers, fallback,
  concurrency, and provider troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Models and Providers

Use this sub-skill when a task involves choosing a Pydantic AI model string, configuring a provider or profile, installing optional provider dependencies, wrapping models for fallback/concurrency/instrumentation, adding provider-native tools, using embeddings, or diagnosing provider import/auth/settings failures.

## Read First

- Read [references/model-selection.md](references/model-selection.md) to choose `provider:model-name` strings, direct model/provider/profile classes, `ModelSettings`, `known_model_names()`, `FallbackModel`, `ConcurrencyLimitedModel`, and `InstrumentedModel`.
- Read [references/provider-installation.md](references/provider-installation.md) to map model strings, providers, embeddings, and common tools to the smallest `pydantic-ai-slim[...]` extra and environment-variable checklist.
- Read [references/native-tools-and-embeddings.md](references/native-tools-and-embeddings.md) when adding provider-native `WebSearchTool`, `CodeExecutionTool`, `MCPServerTool`, `FileSearchTool`, embedding workflows, or common tools that require extras.
- Read [references/troubleshooting.md](references/troubleshooting.md) to debug missing provider prefixes, optional SDK imports, API keys, Google/Vertex naming, profile/schema incompatibilities, fallback timing, and native-tool failures.
- Run [scripts/check_optional_provider.py](scripts/check_optional_provider.py) for a no-network import/config diagnostic for selected model, embedding, or common-tool providers.

## Route Elsewhere

- Use `../agent-core/` for `Agent` construction, run modes, dependencies, streaming, message history, and deterministic `TestModel`/`FunctionModel` testing.
- Use `../tools-and-toolsets/` for Python function tools, tool schemas, toolsets, approvals, deferred tools, and `ModelRetry` design.
- Use `../outputs-and-messages/` for `NativeOutput`, structured output support, message parts, multimodal content, and output/history serialization.
- Use `../mcp-and-integrations/` for MCP client/server lifecycles, provider-adaptive capabilities, Logfire, UI adapters, and durable execution integrations.
- Use `../cli-and-apps/` for `clai`, `pai`, web UI, and command-line model flags.

## Operating Rules

- Prefer provider-prefixed strings such as `openai:gpt-5.2`, `anthropic:claude-opus-4-6`, `google:gemini-3-pro-preview`, or `openrouter:google/gemini-3-pro-preview` when portability is enough.
- Instantiate concrete model/provider classes only when customizing authentication, base URLs, HTTP clients, profiles, default settings, retries, or gateway behavior.
- Treat cloud SDKs, credentials, native tools, common web tools, and embeddings as optional: diagnose imports and configuration locally before claiming provider access.
- Do not run cloud verification scripts or upload helpers as part of this runtime skill; credentialed Bedrock, Vertex/GCS, and file-upload scripts are source evidence only and are intentionally excluded.
