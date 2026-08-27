---
name: knowledge-and-ocr
description: "Operate Yuxi knowledge-base, retrieval, document parsing, OCR,
  graph, mindmap, and knowledge evaluation workflows safely."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Yuxi knowledge and OCR operating guide

Load this sub-skill when the task touches Yuxi knowledge bases, RAG retrieval, document upload/parse/chunk/index flows, OCR configuration, graph/mindmap features, knowledge evaluation, KB agent tools, or `read_file` OCR fallback behavior.

## Owned capabilities

- Knowledge-base types: Milvus document KBs, Dify Dataset read-only retrieval connectors, and Notion Data Source read-only retrieval connectors.
- Document lifecycle: upload/import/fetch, file records, parsing to Markdown, chunking/indexing, re-indexing, file search/open/find/download, previews, and image proxy handling.
- Retrieval: vector, keyword/BM25, hybrid, reranker, file-name scoped search, and optional graph-enhanced retrieval for Milvus KBs.
- OCR: default engine resolution, per-file engine selection, config/health endpoints, local/service/cloud engines, and agent `ocr_parse_file` fallback.
- Knowledge structure: mindmap generation/diff/incremental update, generated sample questions, Milvus knowledge graph build/query/reset/reconcile.
- Evaluation: JSONL benchmark upload, LLM-generated benchmarks, RAG evaluation runs, result inspection, and metrics interpretation.

Use sibling sub-skills instead for deployment startup details, CLI command syntax, agent runtime internals unrelated to KB data, or general repo development workflow.

## Safety gates before acting

1. **Classify the runtime need.** Parser facade and metadata checks are CPU-safe; real KB ingestion/retrieval requires running services such as API, Postgres, Redis/task workers, MinIO, and Milvus. Graph build also needs Neo4j and a configured LLM provider. Some OCR engines require GPU services or cloud credentials.
2. **Do not assume credentials.** Dify, Notion, MinerU Official, DeepSeek OCR, PaddleOCR API, rerankers, embeddings, and LLM-based graph/evaluation features may call external services. Confirm credentials and side effects before running them.
3. **Respect file boundaries.** Knowledge files should enter via Yuxi upload/import/fetch APIs and be stored in MinIO before document record creation. Agent OCR fallback only accepts sandbox virtual paths under user-data `workspace`, `uploads`, or `outputs` and writes Markdown under `outputs/ocr`.
4. **Do not treat read-only connectors as Milvus.** Dify and Notion are normal KB types for retrieval, but public document upload/open/find/download workflows are gated to document-supporting KBs; expect read-only connectors to reject file operations.
5. **Keep secrets out of logs and artifacts.** Config APIs intentionally redact sensitive values; never print tokens or API keys while debugging.

## First routing question

Choose the narrow workflow before touching code or services:

- **Create/query/manage a KB:** use [references/knowledge-workflows.md](references/knowledge-workflows.md#knowledge-base-lifecycle-and-entry-points).
- **OCR or parser issue:** use [references/ocr-engine-matrix.md](references/ocr-engine-matrix.md) first, then [references/troubleshooting.md](references/troubleshooting.md#ocr-and-parser-failures).
- **Agent KB tools:** use [references/knowledge-workflows.md](references/knowledge-workflows.md#agent-tool-entry-points).
- **Graph or mindmap:** use [references/knowledge-workflows.md](references/knowledge-workflows.md#mindmap-sample-questions-and-graph-workflows).
- **Knowledge evaluation:** use [references/knowledge-workflows.md](references/knowledge-workflows.md#knowledge-evaluation-workflow).
- **Unknown failure:** use [references/troubleshooting.md](references/troubleshooting.md) and classify by KB type, file status, OCR engine, service dependency, and credential requirement.

## Safe entry points

Prefer these entry points because they preserve Yuxi's permission, config, storage, and task semantics:

- Web/API routes under `/api/knowledge/*`, `/api/system/ocr/*`, `/api/system/config*`, `/api/system/config/options*`, `/api/evaluation/*`, and `/api/graph/*`.
- Python service/facade calls: `yuxi.knowledge.runtime.knowledge_base`, `yuxi.services.ocr_service.parse_document`, `yuxi.services.ocr_service.get_ocr_options`, `yuxi.services.ocr_service.check_all_ocr_health`, and `yuxi.knowledge.graphs.milvus_graph_service.MilvusGraphService`.
- Agent tools made available by the built-in `knowledge-base` skill dependency: `list_kbs`, `get_mindmap`, `query_kb`, `search_file`, `open_kb_document`, `find_kb_document`, and `download_kb_file`.
- Agent built-in OCR helper: `ocr_parse_file` for sandbox PDF/Office/image to Markdown conversion.

Avoid calling low-level parser functions directly unless the task is specifically parser internals. The business entry point is `parse_document`; low-level PDF/image parsers expect an already resolved `ocr_engine` and can bypass DB/environment fallback if called incorrectly.

## Verification candidates

- CPU-safe native candidate: `pytest backend/test/unit/knowledge/test_parser_facade.py` — proves parser registry metadata, engine selection, parser facade, credential-safe cache keys, and common document conversion behavior.
- Service-required candidate: `pytest backend/test/e2e/test_ocr_config_center_e2e.py` — proves configured default OCR drives real temporary attachment parsing when API services and MinIO are available.
- Service/model-required candidate: `pytest backend/test/e2e/test_read_file_multimodal_e2e.py` — proves image `read_file` and non-vision OCR fallback only when model/OCR prerequisites are configured.

Run service-required candidates only after the deployment sub-skill's runtime checks pass and the needed credentials/providers are approved.
