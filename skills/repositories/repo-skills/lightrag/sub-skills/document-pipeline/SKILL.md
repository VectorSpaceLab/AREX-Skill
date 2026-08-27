---
name: document-pipeline
description: "Work with LightRAG document ingestion internals: parser routing,
  filename and process options, chunker selection, sidecars, multimodal analysis
  flow, doc-status metadata, and pipeline concurrency/refusal semantics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LightRAG Document Pipeline

Use this sub-skill when a task involves file/text ingestion behavior, parser routing, process-option strings, chunker strategy selection, sidecar artifacts, multimodal analysis flow, doc-status state metadata, or upload/scan/delete concurrency reasoning.

## Route By Task

- Choose parser engines, filename hints, `LIGHTRAG_PARSER` rules, process options, engine parameters, or chunk parameters with [parser-and-process-options](references/parser-and-process-options.md).
- Compare `F` / `R` / `V` / `P` chunking, understand sidecar artifacts, or reason about fallback/provenance behavior with [chunking-and-sidecars](references/chunking-and-sidecars.md).
- Explain why enqueue, scan, delete, or processing was refused or deferred using [pipeline-concurrency](references/pipeline-concurrency.md).
- Diagnose unavailable parser services, invalid hints/options, missing sidecars, doc-status failures, cancellation, or stale parse/chunk metadata with [troubleshooting](references/troubleshooting.md).
- Run [scripts/check_pipeline_symbols.py](scripts/check_pipeline_symbols.py) for a safe installed-package import and symbol/signature check that does not call parser services, models, credentials, storages, or repository tests.

## Boundaries

- This sub-skill owns `apipeline_enqueue_documents`, `apipeline_process_enqueue_documents`, parse/analyze/process staging, parser routing functions, `process_options`, `chunk_options`, sidecar contracts, multimodal sidecar chunks, doc-status metadata carry-over, and `pipeline_status` fields.
- For direct `LightRAG` construction, `ainsert`, `aquery`, lifecycle, custom KG insertion, embeddings, cache, rerank, and generic library examples, route to `../core-rag/SKILL.md`.
- For API endpoint request/response details, upload route models, WebUI operation, auth, server startup, or deployment, route to `../api-server/SKILL.md`.
- For storage backend selection, database services, migrations, workspace isolation, or destructive storage operations, route to `../storage-backends/SKILL.md`.
- For LLM, VLM, embedding, reranker provider setup, credentials, and provider-specific parameters, route to `../llm-providers/SKILL.md`.

## Non-Negotiables

- Treat `process_options` as the exact per-document selector string: `i`, `t`, `e`, `!`, plus at most one chunk selector from `F` / `R` / `V` / `P`.
- Do not make reusable guidance depend on source-checkout paths, repository scripts, examples, docs, tests, or local environment locations.
- Be explicit when a parser or modality path needs optional dependencies, an external parser service, embeddings, or VLM/LLM roles; do not present those paths as always-available.
- Preserve the concurrency contract: `busy` alone does not block enqueue, but `destructive_busy` and `scanning_exclusive` do.
