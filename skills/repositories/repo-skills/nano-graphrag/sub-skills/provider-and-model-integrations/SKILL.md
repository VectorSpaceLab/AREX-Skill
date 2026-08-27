---
name: provider-and-model-integrations
description: "Configure nano-graphrag LLM and embedding providers safely,
  including OpenAI, Azure OpenAI, Bedrock, OpenAI-compatible APIs, Ollama, local
  embeddings, cache kwargs, and provider pitfalls."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Provider and model integrations

Use this sub-skill when a user needs to configure nano-graphrag LLM or embedding providers, replace the default OpenAI calls, combine hosted LLMs with local embeddings, tune provider concurrency/token limits, or debug provider-specific failures.

## Fast routing

- Default provider path: `GraphRAG()` uses OpenAI chat models (`gpt-4o`, `gpt-4o-mini`) and OpenAI embeddings (`text-embedding-3-small`).
- Built-in switches: use `GraphRAG(..., using_azure_openai=True)` for Azure OpenAI defaults, or `GraphRAG(..., using_amazon_bedrock=True, best_model_id=..., cheap_model_id=...)` for Bedrock chat plus Titan embeddings.
- Custom provider path: pass async `best_model_func`, async `cheap_model_func`, and/or an `EmbeddingFunc`-wrapped `embedding_func` to `GraphRAG`.
- Cache-aware LLM functions must accept `**kwargs`, pop `hashing_kv`, and not forward `hashing_kv` to provider SDK calls.
- Provider SDKs that reject OpenAI-specific kwargs such as `response_format` or `max_tokens` need adapter cleanup before making the request.

## Read or run these files

- Read [references/provider-recipes.md](references/provider-recipes.md) when implementing OpenAI, Azure OpenAI, Bedrock, OpenAI-compatible, DeepSeek-style, Ollama, or hosted-LLM-plus-local-embedding recipes.
- Read [references/embedding-functions.md](references/embedding-functions.md) when writing or validating `embedding_func`, `wrap_embedding_func_with_attrs`, vector shape, dimension, normalization, and batching behavior.
- Read [references/troubleshooting.md](references/troubleshooting.md) when credentials, unsupported kwargs, malformed JSON, Ollama context, Bedrock region/IAM, rate limits, or provider tuning issues appear.
- Run [scripts/provider_template.py](scripts/provider_template.py) with `--help` to print credential-free provider skeletons or inspect a local function shape without calling provider APIs by default.

## Boundaries

- Query-mode semantics, insert/query lifecycle, chunking, and `QueryParam` details belong to `../core-graphrag-workflows/`.
- Storage adapters and vector-store class selection belong to `../storage-backends/`.
- Prompt editing, JSON repair internals, DSPy entity extraction, and empty-graph root-cause analysis belong to `../customization-and-troubleshooting/`; this sub-skill cross-links there when provider output format is the likely cause.
