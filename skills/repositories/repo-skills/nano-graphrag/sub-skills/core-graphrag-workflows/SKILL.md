---
name: core-graphrag-workflows
description: "Operate nano-graphrag's core GraphRAG lifecycle: construct
  GraphRAG, insert documents, query modes, async use, persistence, chunking, and
  safe no-network smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# core-graphrag-workflows

Use this sub-skill when a task needs the core `nano_graphrag` lifecycle: import sanity, `GraphRAG` construction, document insertion, local/global/naive querying, async equivalents, `working_dir` persistence, chunking/tokenizer behavior, or context-only retrieval.

Do not use this sub-skill for provider-specific LLM/embedding implementations, storage backend selection, prompt/entity-extraction customization, DSPy extraction, or JSON repair details. Route those to the sibling sub-skills `provider-and-model-integrations`, `storage-backends`, and `customization-and-troubleshooting`.

## References and scripts

- Read [references/core-api.md](references/core-api.md) when you need verified constructor/method signatures, dataclass defaults, query-mode semantics, chunk-function contracts, token-budget fields, or default `working_dir` artifacts.
- Read [references/workflows.md](references/workflows.md) when you need self-contained recipes for quick start, fake no-network LLM/embedding patterns, batch or incremental insert, async use, persistence/reload, context-only retrieval, or custom chunking validation.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a core workflow raises a query-mode guard, produces empty graph/Leiden symptoms, fails around tokenizers/chunk functions, needs the missing-`transformers` import repair, or behaves unexpectedly after reload.
- Run [scripts/core_smoke.py](scripts/core_smoke.py) to validate that the installed package imports, constructs `GraphRAG` with deterministic fake functions, chunks text, enforces query-mode guards, and completes a no-network insert/query/reload smoke.

## Operating checklist

1. Start with `from nano_graphrag import GraphRAG, QueryParam`; if import fails with `ModuleNotFoundError: No module named 'transformers'`, install `transformers` in the active environment before debugging GraphRAG itself.
2. Pick a stable `working_dir` for persistent indexes; reusing the same directory reloads default JSON/vector/GraphML artifacts.
3. Provide or route to provider-specific `best_model_func`, `cheap_model_func`, and `embedding_func` before inserting real documents; the defaults are hosted-provider oriented.
4. Use `insert`/`ainsert` for one string or a list of strings; duplicate docs/chunks are skipped by content hash, while community reports are regenerated on non-empty incremental inserts.
5. Query with `QueryParam(mode="global")` by default, `mode="local"` only when `enable_local=True`, and `mode="naive"` only when `enable_naive_rag=True` was enabled before inserting content into the vector index.
6. For retrieval context without final response generation, pass `QueryParam(..., only_need_context=True)` and confirm the selected mode is enabled.
