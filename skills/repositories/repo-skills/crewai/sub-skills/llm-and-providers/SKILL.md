---
name: llm-and-providers
description: "Guides agents configuring CrewAI LLM providers, model strings,
  credentials, base URLs,
  Azure/OpenAI-compatible/Anthropic/Bedrock/Google/Snowflake settings,
  streaming, tool calls, custom BaseLLM implementations, and LiteLLM migration
  caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LLM and Providers

Use this sub-skill when the task is to configure, validate, migrate, or troubleshoot CrewAI `LLM` objects, provider model strings, API keys, base URLs, structured responses, tool-calling LLM behavior, streaming LLM behavior, context windows, rate-limit knobs, or custom `BaseLLM` implementations.

## Read First

- [Provider reference](references/provider-reference.md) for the current `LLM` constructor shape, provider dispatch rules, model prefixes, credentials, base URL handling, Azure/OpenAI-compatible/Anthropic/Bedrock/Google/Snowflake examples, context-window notes, and LiteLLM fallback rules.
- [Custom LLM](references/custom-llm.md) for implementing `BaseLLM`, required `call()`/`acall()` contracts, function calling, stop words, context windows, error handling, and safe test doubles.
- [Streaming and tool calls](references/streaming-and-tool-calls.md) for `stream=True`, direct `LLM.call()`/`acall()`, Crew/Flow streaming outputs, `function_calling_llm`, response models, and provider compatibility trade-offs.
- [Troubleshooting](references/troubleshooting.md) for missing API keys, wrong prefixes, OpenAI-compatible base URL confusion, streaming/tool-call incompatibility, `response_format` misuse, multimodal mismatch, rate limits, context windows, and LiteLLM migration mistakes.
- [Offline config checker](scripts/check_llm_config.py) for a no-network diagnostic of model/provider/base URL/env-var choices; run `python scripts/check_llm_config.py --help` before using it.

## Boundaries

- Stay here for `LLM(...)` parameters, provider selection, credentials, API keys, base URLs, `api_version`, structured response formats, streaming, direct LLM calls, tool-call provider compatibility, custom LLM classes, and LiteLLM migration.
- Use [../core-runtime/SKILL.md](../core-runtime/SKILL.md) for where to attach `llm`, `manager_llm`, `planning_llm`, `chat_llm`, or `function_calling_llm` on `Agent`, `Crew`, and project runtime definitions.
- Use [../tools-and-mcp/SKILL.md](../tools-and-mcp/SKILL.md) for implementing CrewAI tools, MCP adapters, and tool schema design beyond LLM provider support.
- Use [../files-and-multimodal/SKILL.md](../files-and-multimodal/SKILL.md) for file input payload shapes, upload/cache behavior, MIME constraints, and provider-specific file limits.
- Use [../observability-and-hooks/SKILL.md](../observability-and-hooks/SKILL.md) for tracing, event listeners, transport interceptors, and observability integrations around LLM calls.
- Return to [../../SKILL.md](../../SKILL.md) when a request spans multiple CrewAI capability areas and needs root routing context.

## Safe Defaults

- Prefer explicit `LLM(model="provider/model-name", ...)` objects for non-trivial configuration; plain strings are fine only when defaults and environment variables are already correct.
- Prefer native providers (`openai`, `anthropic`, `gemini`/`google`, `azure`, `bedrock`, `snowflake`, and built-in OpenAI-compatible providers) before adding `crewai[litellm]`.
- Never print, commit, or hard-code real API keys. Use environment variable names or placeholders in examples.
- Validate configuration offline with [scripts/check_llm_config.py](scripts/check_llm_config.py) before running crews that may make network or LLM calls.
