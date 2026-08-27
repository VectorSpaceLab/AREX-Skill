---
name: model-providers
description: "Configure and troubleshoot Kotaemon LLM, embedding, reranking,
  web-search, local-model, and GraphRAG providers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Kotaemon Model Providers

Use this sub-skill when a task involves Kotaemon model/provider setup: LLMs, embeddings, rerankers, local model servers, OpenAI-compatible endpoints, web search credentials, or GraphRAG model configuration.

## Use This For

- Mapping `.env`, `flowsettings.py`, Resources UI, and manager database entries to provider specs for LLM, embedding, and reranking models.
- Configuring OpenAI, Azure OpenAI, Ollama, OpenAI-compatible local servers, `llama-cpp-python`/GGUF, Cohere, VoyageAI, Google, Mistral, Groq, Anthropic, TEI, HuggingFace, and FastEmbed options.
- Checking required credential pairs, endpoint suffixes, placeholder keys, optional provider packages, and Docker host-vs-localhost URL mistakes without making network calls.
- Enabling or diagnosing GraphRAG, NanoGraphRAG, LightRAG, custom GraphRAG settings, and local GraphRAG model URLs.
- Configuring Tavily or Jina web-search retrievers and reranker provider entries.

## Route Elsewhere

- Use `../app-deployment/SKILL.md` for Docker/local launch, Gradio login, app data, PDF.js, update, migration, or general `.env` deployment checks.
- Use `../rag-core/SKILL.md` for programmatic RAG composition, `Document`/`RetrievedDocument`, vector index APIs, retrieval pipelines, reranker execution inside retrieval, QA, citations, and reasoning.
- Use `../document-ingestion/SKILL.md` for file readers, OCR/table parsers, splitters, metadata validation, and parser optional dependencies.
- Use `../extensions/SKILL.md` for adding custom providers, extra vendors, pages, components, templates, or plugin UI integrations.

## Fast Path

1. Decide where the provider is configured: `.env` seeds `flowsettings.py`; the Resources UI persists LLM, embedding, and reranking entries after the app database exists.
2. Use `references/provider-configuration.md` to map provider choices to exact keys, manager names, class types, UI fields, and required packages.
3. For local/private RAG, use `references/local-models.md` before changing URLs: OpenAI-compatible entries use `/v1/`; native Ollama chat uses the non-`/v1/` Ollama base.
4. For graph indexes, use `references/graphrag.md` to choose MS GraphRAG vs NanoGraphRAG vs LightRAG and verify toggles, API key strategy, and custom settings.
5. Run the safe validator before launch or UI testing:

```bash
python scripts/check_provider_env.py --env-file .env --select openai --select embeddings
```

## Safety Rules

- Do not print secrets, call provider APIs, start model servers, pull Ollama models, download GGUF weights, install optional packages, or index data unless the user explicitly approves side effects.
- Treat placeholders such as `<YOUR_OPENAI_KEY>`, `your-key`, `dummy`, and empty strings as not configured unless they are intentionally used for a local OpenAI-compatible endpoint.
- Validate endpoint shapes separately from connectivity; this sub-skill's bundled script is offline-only.
- Remember that `.env` registration is not the only source of truth after first run: existing app database rows in the Resources UI can override or outlive changed environment values.

## Difficult Cases

- Ollama chat plus embeddings: configure two OpenAI-compatible entries with `/v1/` base URLs, `api_key: ollama`, and distinct chat/embedding model names; use `references/local-models.md` and the offline validator before trying network calls.
- GraphRAG/local-model diagnosis: validate `GRAPHRAG_API_KEY`, `USE_CUSTOMIZED_GRAPHRAG_SETTING`, local model base URLs, and `settings.yaml` shape without calling external services; route app launch fixes to `../app-deployment/SKILL.md`.

## Bundled References

- `references/provider-configuration.md` - provider map for env keys, class specs, managers, UI fields, web search, reranking, and optional packages.
- `references/local-models.md` - Ollama, Docker host URLs, OpenAI-compatible local servers, GGUF/`llama-cpp-python`, and local RAG tuning.
- `references/graphrag.md` - MS GraphRAG, NanoGraphRAG, LightRAG, toggles, custom settings, and model dependencies.
- `references/troubleshooting.md` - provider failure-mode decision tree and safe remediation steps.

## Bundled Script

```bash
python skills/kotaemon/sub-skills/model-providers/scripts/check_provider_env.py --env-file .env --select auto
```

The validator reads `.env`-style files plus inherited environment values, redacts all key-like values, performs no network calls, and exits nonzero when selected providers have missing required pairs, placeholder keys, incompatible URL suffixes, or missing local GGUF paths.
