---
name: llm-provider-config
description: "Configure direct LLM, embedding, and model-provider access for
  Langroid agents without mixing in agent orchestration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# llm-provider-config

Use this sub-skill when the task is to choose, build, validate, or troubleshoot Langroid LLM and embedding provider configuration. Stay at the provider-access layer: `OpenAIGPTConfig`, `OpenAIGPT`, `AzureConfig`, provider model strings, OpenAI-compatible `api_base` endpoints, API-key handling, HTTP clients, streaming/reasoning flags, and embedding config classes.

## Scope boundary

- Include direct LLM access, OpenAI-compatible bases, Azure, Gemini, LiteLLM proxy, LiteLLM adapter strings, Ollama/local servers, OpenRouter-style gateways, Portkey, LangDB, rotating API keys, cached clients, HTTP client config, and embedding provider configs.
- Exclude agent design, task loops, tool messages, function-calling workflows, and prompt orchestration; route those to `../agents-tasks-tools/SKILL.md`.
- Exclude RAG/vector-store wiring beyond selecting an embedding config; route retrieval or document-chat wiring to `../retrieval-doc-chat/SKILL.md`.
- Exclude MCP server/tool integration; route it to `../integrations-mcp-chainlit/SKILL.md`.

## Operating procedure

1. Identify whether the user needs an LLM config, an embedding config, or both.
2. Choose the smallest direct provider path before adding a proxy or gateway:
   - native OpenAI or Azure when the deployment is actually OpenAI/Azure;
   - provider prefix such as `gemini/`, `openrouter/`, `ollama/`, `vllm/`, `llamacpp/`, `langdb/`, or `portkey/` when Langroid has a first-class path;
   - explicit `api_base` for a generic OpenAI-compatible endpoint;
   - `litellm-proxy/` only for a deployed LiteLLM proxy server;
   - `litellm/` only for the local LiteLLM adapter library.
3. Validate model string, API-key source, base URL shape, timeout/temperature/output-token settings, cache behavior, and optional HTTP-client needs before any generation call.
4. For embeddings, configure only the embedding provider and dimensions here; leave collection/index/vector-store construction to the retrieval sub-skill.
5. Use the bundled smoke script for no-network sanity checks when a config looks suspicious.

## Bundled references

- [Provider configuration](references/provider-config.md): LLM config fields, provider prefixes, Azure, gateway parameters, caching, HTTP clients, rotating credentials, and reasoning content.
- [Embedding configuration](references/embedding-config.md): OpenAI, Azure OpenAI, Gemini, LangDB, SentenceTransformer, FastEmbed, and llama.cpp-server embedding configs.
- [Model selection](references/model-selection.md): choosing strings/enums, direct vs proxy access, local-server forms, formatter suffixes, and environment-prefix pitfalls.
- [Troubleshooting](references/troubleshooting.md): missing keys, bad bases, Azure deployment names, Gemini/Vertex base handling, LiteLLM confusion, key rotation, client caching, and optional embedding dependencies.

## No-network smoke check

Run:

```bash
python scripts/provider_config_smoke.py
```

The script sanitizes provider environment variables for deterministic output, constructs representative provider and embedding configs, avoids `chat()`, `generate()`, and embedding calls, and falls back to a static source-derived check if optional runtime dependencies are not installed. Use `--help` for options.
