---
name: models-providers
description: "Configure OpenAI Agents Python model settings, OpenAI providers,
  Responses websocket transport, third-party adapters, retries, and
  multi-provider routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Models & Providers

Use this sub-skill when configuring model selection, provider routing, OpenAI Responses vs Chat Completions, Responses websocket transport, `ModelSettings`, model retries, LiteLLM, any-llm, or OpenAI-compatible endpoints.

## Read First

- Start with [references/provider-reference.md](references/provider-reference.md) for the model/provider classes, settings fields, environment variables, transport choices, and optional extras.
- Use [references/workflows.md](references/workflows.md) for copyable setup patterns: default OpenAI, websocket reuse, custom OpenAI-compatible endpoints, `MultiProvider` prefix modes, LiteLLM/any-llm, retries, and feature validation.
- Use [references/troubleshooting.md](references/troubleshooting.md) for API key errors, wrong API path, websocket keepalive/message-size issues, Chat Completions feature gaps, namespaced model IDs, missing optional extras, and reasoning-content replay.
- Run [scripts/inspect_model_provider.py](scripts/inspect_model_provider.py) for a local no-API-call import/configuration check that masks secret values and reports optional adapter availability.

## Routing Boundaries

- Stay here for `ModelSettings`, `OpenAIProvider`, `OpenAIResponsesModel`, `OpenAIChatCompletionsModel`, `responses_websocket_session()`, `MultiProvider`, LiteLLM, any-llm, model retries, feature validation, and reasoning-content model adapter caveats.
- Route realtime model sessions, `RealtimeAgent`, `RealtimeRunner`, audio, and voice optional extras to [../realtime-voice/SKILL.md](../realtime-voice/SKILL.md).
- Route runner loop behavior, handoffs, sessions, `RunState`, guardrails, tool execution, and turn limits to [../core-runtime/SKILL.md](../core-runtime/SKILL.md).
- Route tracing processors, trace export keys, trace metadata, and sensitive trace payload controls to [../tracing-observability/SKILL.md](../tracing-observability/SKILL.md).

## Fast Decisions

- Prefer the default OpenAI Responses path for OpenAI models and Responses-only tools.
- Use Chat Completions only for providers/endpoints that do not support Responses, and enable strict feature validation while migrating.
- Use `responses_websocket_session()` for multi-turn Responses websocket workflows that should reuse one websocket-capable provider/run config.
- Use `MultiProvider(openai_prefix_mode="model_id", unknown_prefix_mode="model_id")` when an OpenAI-compatible endpoint expects literal namespaced model IDs.
- Use LiteLLM or any-llm only when their adapter coverage/routing is needed; validate the exact upstream provider feature set before relying on structured outputs, tools, usage, or Responses-only behavior.
