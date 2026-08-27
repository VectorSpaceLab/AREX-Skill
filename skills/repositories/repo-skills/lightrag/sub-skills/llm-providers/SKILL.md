---
name: llm-providers
description: "Configure and troubleshoot LightRAG LLM, embedding, VLM,
  role-specific LLM, rerank, asymmetric embedding, provider binding, and
  cache-identity behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LightRAG LLM Providers

Use this sub-skill when work involves LightRAG model providers, embedding wrappers, VLM image input support, role-specific LLM routing, reranking, provider options, credentials, service endpoints, asymmetric embeddings, or LLM cache identity.

## Route by Task

- Choose LLM, embedding, or VLM bindings with [provider-reference.md](references/provider-reference.md).
- Configure role-specific models or rerankers with [role-and-rerank-reference.md](references/role-and-rerank-reference.md).
- Diagnose provider, credential, prefix, cache, VLM, or rerank failures with [troubleshooting.md](references/troubleshooting.md).
- Verify installed LightRAG LLM symbols without network calls with `python scripts/check_llm_symbols.py`, or use `--json` for machine-readable output.

## Boundaries

- This sub-skill owns `lightrag.llm` provider bindings, `EmbeddingFunc`, `wrap_embedding_func_with_attrs`, role LLM configuration, API binding options, rerank bindings, asymmetric embedding configuration, VLM image inputs, response-format compatibility, and LLM cache identity.
- For storage cache cleanup, vector rebuilds, workspace data drops, and embedding dimension mismatch repair operations, route to `../storage-backends/SKILL.md`.
- For parser multimodal workflows, parsed artifact routing, and document ingestion orchestration, route to `../document-pipeline/SKILL.md`.
- For API server env file mechanics, deployment, REST routes, and WebUI behavior, route to `../api-server/SKILL.md`.
- For insert/query lifecycle, `LightRAG` initialization, `QueryParam`, and core RAG application flow, route to `../core-rag/SKILL.md`.

## Non-Negotiables

- Never run provider checks that call live LLM, embedding, VLM, or rerank APIs unless the user explicitly provides credentials, service targets, and permission.
- Keep reusable examples free of secrets, live service targets, and machine-specific details.
- Use `.func` when wrapping an already-decorated embedding function inside a new `EmbeddingFunc` to avoid nested wrapper conflicts.
- Changing embedding provider, model, dimension, `model_name`, or asymmetric behavior changes vector semantics; plan vector rebuild or re-index work with the storage skill area.
- Bedrock auth uses AWS SigV4 fields or process-level Bedrock bearer-token auth, not generic LightRAG API-key fields.
