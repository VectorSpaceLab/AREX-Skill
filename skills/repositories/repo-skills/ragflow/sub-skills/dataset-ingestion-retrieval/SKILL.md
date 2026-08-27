---
name: dataset-ingestion-retrieval
description: "Work on RAGFlow dataset/document/chunk ingestion, parser_config,
  task execution, retrieval, RAPTOR, and GraphRAG behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Dataset Ingestion Retrieval

Use this sub-skill when changing or debugging RAGFlow's dataset, document, chunk, parser configuration, indexing task, retrieval, RAPTOR, or GraphRAG behavior.

## Start Here

1. Identify the seam: REST request handling, parser configuration, task execution, document engine indexing, retrieval ranking, or graph/RAPTOR augmentation.
2. Check the relevant reference before editing:
   - `references/ingestion-pipeline.md` for built-in chunking, ingestion pipelines, task routes, embedding/indexing, RAPTOR, and GraphRAG execution.
   - `references/retrieval-and-graphrag.md` for hybrid search, metadata filters, child/TOC retrieval, KG retrieval, page rank, and retrieval response mapping.
   - `references/data-formats.md` for request fields, parser_config keys, chunk fields, metadata condition shape, and index fields.
   - `references/troubleshooting.md` for common no-chunk, stuck-task, model, queue, RAPTOR, and GraphRAG failures.
3. For parser_config changes, run the bundled offline helper on example JSON before touching service code:
   - `python scripts/inspect_parser_config.py --chunk-method naive --config parser_config.json`
   - `python scripts/inspect_parser_config.py --document-name example.pdf --config parser_config.json`

## Scope Boundaries

- Include dataset/document/chunk lifecycle, `parser_config`, ingestion dataflow, task executor behavior, `Dealer` retrieval, GraphRAG/RAPTOR, metadata filters, and API handoffs.
- Exclude DeepDoc parser internals; use the document parsing sub-skill for parser implementation details.
- Exclude public SDK client recipes; use the SDK/HTTP integration sub-skill for end-user client examples.
- Exclude deployment/service startup; use the deployment/configuration sub-skill for Redis, NATS, MySQL, MinIO, Elasticsearch/Infinity startup.
- Frontend form changes should stay minimal here and cross-check the frontend integration sub-skill.

## High-Value Checks

- Preserve the alias contract: public `chunk_method` maps to internal `parser_id`, and public `embedding_model` maps to internal `embd_id`.
- Keep dataset and document parser config merge semantics intact: dataset updates deep-merge config, document updates merge ext fields into the document config, and reparse paths may apply KB metadata config.
- For retrieval fixes, verify both `/retrieval` and dataset search endpoints when behavior is shared.
- For GraphRAG/RAPTOR changes, verify task routing, cleanup/resume behavior, and document-engine field names, not just prompt/config defaults.

## Native Verification Candidates

Prefer safe, focused tests around metadata filters, search pagination, rank feature scores, GraphRAG checkpoints/phase markers, and REST task routes for dataset/document/chunk/retrieval behavior.

## Difficult Usability Cases

- Diagnose retrieval returning no chunks even though documents show parsed, by tracing document status, doc engine index existence, embedding vector dimensions, dataset/document filters, metadata conditions, and hybrid score thresholds.
- Add a new chunk method end-to-end by tracing parser_config defaults, REST validation, task executor parser selection, frontend form alignment, and SDK/API documentation impact.
