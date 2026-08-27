# Knowledge workflows

This reference distills Yuxi's KB, retrieval, graph, mindmap, OCR-adjacent file, and evaluation behavior into operational steps. Use it with the router in `../SKILL.md`.

## Capability boundaries

| Area | Yuxi owner | Runtime requirement | Key limits |
| --- | --- | --- | --- |
| Milvus KB | Document storage, parse, chunk, index, retrieve, file operations, mindmap, graph, evaluation | API, Postgres, Redis/tasker, MinIO, Milvus, embedding provider | Requires `embedding_model_spec`; file operations only after permission checks; graph is optional |
| Dify KB | Read-only retrieval through Dify Dataset Retrieve API | API plus Dify URL/token/dataset | No upload, parse, index, file tree, open, find, or download through normal public document gates |
| Notion KB | Read-only retrieval from a Notion Data Source | API plus Notion token/data source | Public KB document gates still treat it as read-only; Notion token may come from env or saved params |
| OCR parser facade | Convert supported files to Markdown | CPU for local parsers; optional services/cloud for specialized engines | Use `parse_document`; images require OCR enabled; cloud engines need explicit credentials |
| Knowledge graph | Entity/triple extraction, Neo4j graph, graph vector stores, graph retrieval fusion | Milvus KB chunks, Neo4j, Milvus, embedding provider, LLM extractor | Only Milvus KBs; extractor config is locked; no arbitrary full prompt override |
| Evaluation | JSONL benchmarks, generated datasets, evaluation runs, metrics | Milvus KB chunks, tasker, optional LLM/judge models | Generated dataset currently supports Milvus; graph-enhanced generation requires completed graph index |

## Knowledge-base lifecycle and entry points

### 1. Discover supported KB types and defaults

Safe API probes:

```text
GET /api/knowledge/types
GET /api/knowledge/chunk-presets
GET /api/knowledge/databases/accessible
GET /api/system/ocr/options
GET /api/system/ocr/health
```

The supported KB types are:

- `milvus`: document-supporting RAG KB with vector/BM25/hybrid retrieval.
- `dify`: read-only Dify Dataset connector.
- `notion`: read-only Notion Data Source connector.

### 2. Create a knowledge base

Use `POST /api/knowledge/databases` with these core fields:

```json
{
  "database_name": "Product docs",
  "description": "Source-of-truth product documentation for support answers",
  "kb_type": "milvus",
  "embedding_model_spec": "provider:model",
  "llm_model_spec": null,
  "additional_params": {},
  "share_config": {"version": 2, "read_scope": {"access_level": "global", "department_ids": [], "user_uids": []}, "manage_scope": null}
}
```

Operational rules:

- Milvus requires an embedding model whose model type is `embedding`.
- Dify requires `dify_api_url` ending in `/v1`, `dify_token`, and `dify_dataset_id` in `additional_params`.
- Notion requires `notion_data_source_id` and either `notion_token` or an environment token (`NOTION_TOKEN`/`NOTION_API_KEY`).
- Permissions are stored in version-2 `share_config`. Normal users only see KBs permitted by role/department/user settings.
- `additional_params` for document KBs receives chunk defaults. Do not write legacy root-level `chunk_size`, `chunk_overlap`, or `qa_separator`; use `chunk_preset_id` and `chunk_parser_config`.

### 3. Upload, import, or fetch source files

Preferred source routes:

```text
POST /api/knowledge/files/upload?kb_id=<kb_id>        # multipart upload to MinIO
POST /api/knowledge/files/import-workspace           # import current user's workspace files
POST /api/knowledge/files/fetch-url                  # fetch whitelisted URL as HTML
GET  /api/knowledge/files/supported-types
```

Supported knowledge upload extensions include text/Markdown, DOCX, HTML/HTM, JSON, CSV, XLS/XLSX, PDF, PPTX, image formats (`jpg`, `jpeg`, `png`, `bmp`, `tiff`, `tif`), and ZIP. Normal upload and workspace import enforce a 100 MB per-file limit. URL fetch requires the URL whitelist feature and rejects unsafe/private targets.

The upload/fetch/import response provides a MinIO URL plus `content_hash`, filename, and size. Programmatic ingestion must preserve the content hash because document-record creation validates that every MinIO item has a hash.

### 4. Add records, parse, and index

There are two patterns:

**Explicit staged workflow**

```text
POST /api/knowledge/databases/{kb_id}/documents/add       # create records only
POST /api/knowledge/databases/{kb_id}/documents/parse     # parse selected file_ids
POST /api/knowledge/databases/{kb_id}/documents/index     # index selected file_ids
POST /api/knowledge/databases/{kb_id}/documents/parse-pending
POST /api/knowledge/databases/{kb_id}/documents/index-pending
```

**Single queued ingest workflow**

```text
POST /api/knowledge/databases/{kb_id}/documents
```

with body fields `items` and `params`. Set `params.auto_index=true` to parse then index in one background task.

Important lifecycle states:

1. `uploaded`: file metadata exists; original file is in MinIO.
2. `parsing`: parse task has claimed the file.
3. `parsed`: Markdown was written to MinIO and recorded as `markdown_file`.
4. `error_parsing`: parser/OCR failed; re-parse is allowed.
5. `indexing`: index task has claimed the file.
6. `indexed`: chunks are in PostgreSQL and vectors/BM25 records are in Milvus.
7. `error_indexing`: chunk/index failed; re-index is allowed.

Direct selected parse/index calls accept at most 1000 file IDs. Pending-status jobs batch through server-side cursors and return task IDs.

### 5. Chunking and indexing details

Use these current fields for parse/index parameters:

```json
{
  "ocr_engine": "rapid_ocr",
  "chunk_preset_id": "general",
  "chunk_parser_config": {
    "chunk_token_num": 512,
    "delimiter": "\n",
    "embed_model_id": "provider:model"
  }
}
```

Chunk presets include `general`, `qa`, `book`, `laws`, `semantic`, and `separator`. The parser snapshot is saved per file in `processing_params`; runtime OCR endpoints and credentials are not copied into the file snapshot. Milvus indexing double-writes chunks to PostgreSQL (`knowledge_chunks`) and Milvus; on a double-write failure it attempts to roll back both stores. Re-indexing deletes the file's prior chunks and graph data before inserting replacements.

Milvus schema and retrieval facts:

- Dense vector field uses COSINE similarity.
- The `content` field is analyzed with Chinese analyzer params and has a Milvus BM25 sparse field.
- Query modes: `vector`, `keyword`, and `hybrid`.
- Hybrid uses weighted vector/BM25 ranking; default weights are vector 0.7 and BM25 0.3.
- Optional reranker requires a reranker model when `use_reranker=true`.
- File-name scoped retrieval is implemented by resolving matching file IDs and applying a Milvus filter expression.

## Query, file browsing, and retrieval tuning

Safe API entry points:

```text
POST /api/knowledge/databases/{kb_id}/query
POST /api/knowledge/databases/{kb_id}/query-test
GET  /api/knowledge/databases/{kb_id}/query-params
PUT  /api/knowledge/databases/{kb_id}/query-params
GET  /api/knowledge/databases/{kb_id}/documents
GET  /api/knowledge/databases/{kb_id}/documents/search
GET  /api/knowledge/databases/{kb_id}/documents/{doc_id}/basic
GET  /api/knowledge/databases/{kb_id}/documents/{doc_id}/content
GET  /api/knowledge/databases/{kb_id}/documents/{doc_id}/download
POST /api/knowledge/databases/{kb_id}/stats/repair
```

Useful query options for Milvus:

| Option | Meaning |
| --- | --- |
| `search_mode` | `vector`, `keyword`, or `hybrid` |
| `final_top_k` | final chunk count returned to UI/agent |
| `similarity_threshold` | score threshold, usually 0-1 |
| `bm25_top_k` / `bm25_drop_ratio_search` | BM25 candidate count and sparse-term drop ratio |
| `vector_weight` / `bm25_weight` | hybrid fusion weights |
| `use_reranker` / `reranker_model` / `recall_top_k` | reranker flow and candidate depth |
| `use_graph_retrieval` plus `graph_*` options | entity/triple/PPR graph retrieval fusion |
| `include_distances` | expose raw distance/similarity fields |
| `file_name` | temporary query-time file-name filter |

If retrieval quality is poor, first inspect whether the source files are `indexed`, whether chunks exist, and whether query params changed. Only then tune chunk preset/config, embedding model, search mode, similarity threshold, reranker, or graph retrieval.

## Agent tool entry points

The KB tools are category `knowledge` and are loaded by the built-in `knowledge-base` skill dependency instead of being registered into every agent by default.

| Tool | Use when | Main output/limit |
| --- | --- | --- |
| `list_kbs` | Need accessible KB IDs and descriptions in the current agent session | Returns only KBs visible/enabled for the runtime context |
| `get_mindmap` | Need a KB-level file/category outline | Requires a generated mindmap; looks up by KB name |
| `query_kb` | Need semantic/keyword/hybrid retrieval | Returns structured `kb_id`, `file_id`, chunk IDs, source names, scores |
| `search_file` | Need to find files by filename across visible document-supporting KBs | Requires `kb_name` or `query`; read-only connectors are excluded from file search |
| `open_kb_document` | Need a line-window around parsed Markdown after `query_kb` | Requires document-supporting KB and parsed Markdown; default window is large but capped |
| `find_kb_document` | Need keyword/regex windows inside one known file | Requires document-supporting KB and parsed Markdown |
| `download_kb_file` | Need the original binary in sandbox `outputs` for code-level processing | Writes only into sandbox outputs; strips directories from `save_as` to prevent traversal |

Recommended agent flow:

1. Call `list_kbs` and pick a KB by `kb_id`, not just by display name.
2. Call `query_kb` with a precise query. If results are vague, tune `file_name`, search mode, or query text.
3. Use `open_kb_document` or `find_kb_document` with returned `file_id` for evidence-bearing context.
4. Use `download_kb_file` only when the original binary structure is needed; otherwise prefer parsed Markdown windows.

## Mindmap, sample questions, and graph workflows

### Mindmap

Milvus KB detail pages and APIs can generate a hierarchical mindmap from file metadata. Generation reads file names/types, not full document summaries; current logic caps the file list used in one prompt to the first 20 files to avoid overlong prompts. Incremental update uses a diff between current files and tracked mindmap file IDs. Pure deletion updates can be applied without an AI call, and successful single/batch document deletes remove corresponding leaves from the saved snapshot.

Entry points:

```text
GET  /api/knowledge/mindmap/databases
GET  /api/knowledge/databases/{kb_id}/mindmap/files
POST /api/knowledge/databases/{kb_id}/mindmap/generate
GET  /api/knowledge/databases/{kb_id}/mindmap
GET  /api/knowledge/databases/{kb_id}/mindmap/diff
POST /api/knowledge/databases/{kb_id}/sample-questions
GET  /api/knowledge/databases/{kb_id}/sample-questions
```

Generated sample questions are based on file metadata and are useful for retrieval testing suggestions; they are not full-document summaries.

### Knowledge graph

Graph features are Milvus-KB-specific. The graph build flow extracts entities/relations from indexed chunks, writes graph structure to Neo4j and PostgreSQL, indexes unique graph entities/triples in Milvus, then optionally uses graph retrieval fusion during KB query.

Graph build sequence:

1. Confirm KB type is `milvus` and chunks are indexed.
2. Configure graph extraction:

```text
POST /api/knowledge/databases/{kb_id}/graph-build/config
```

Use `extractor_type="llm"` with `extractor_options.model_spec`. A `schema` is allowed to constrain extraction. A full custom `prompt` is rejected. `concurrency_count` must be an integer from 1 to 1000.

3. Start build:

```text
POST /api/knowledge/databases/{kb_id}/graph-build/index
```

Only one active graph task per KB is allowed.

4. Inspect status/failures:

```text
GET /api/knowledge/databases/{kb_id}/graph-build/status
GET /api/knowledge/databases/{kb_id}/graph-build/failed-chunks
```

5. Reset or reconcile if needed:

```text
POST /api/knowledge/databases/{kb_id}/graph-build/reset
POST /api/knowledge/databases/{kb_id}/graph-build/reconcile
```

Graph visualization/query routes:

```text
GET /api/graph/list
GET /api/graph/subgraph?kb_id=<kb_id>&node_label=<keyword>&max_depth=2&max_nodes=100
GET /api/graph/labels?kb_id=<kb_id>
GET /api/graph/stats?kb_id=<kb_id>
```

Graph retrieval tuning uses query params such as `use_graph_retrieval`, `graph_entity_top_k`, `graph_triple_top_k`, `graph_top_k`, `graph_max_nodes`, `graph_weight`, and `ppr_damping`.

## Knowledge evaluation workflow

Manual benchmark JSONL rows use this shape:

```json
{"query": "What is the policy?", "gold_chunk_ids": ["chunk_001"], "gold_answer": "The policy is ..."}
```

`query` is required. `gold_chunk_ids` enables retrieval metrics; `gold_answer` enables answer metrics if a judge/answer model is supplied.

Entry points:

```text
POST   /api/evaluation/databases/{kb_id}/datasets/upload
GET    /api/evaluation/databases/{kb_id}/datasets
GET    /api/evaluation/databases/{kb_id}/datasets/{dataset_id}
GET    /api/evaluation/datasets/{dataset_id}/download
DELETE /api/evaluation/datasets/{dataset_id}
POST   /api/evaluation/databases/{kb_id}/datasets/generate
POST   /api/evaluation/databases/{kb_id}/datasets/{dataset_id}/resume
POST   /api/evaluation/databases/{kb_id}/runs
GET    /api/evaluation/databases/{kb_id}/runs
GET    /api/evaluation/databases/{kb_id}/runs/{run_id}
DELETE /api/evaluation/databases/{kb_id}/runs/{run_id}
```

Generated benchmark datasets:

- Require a Milvus KB with chunks.
- Accept `count`, `neighbors_count`, `concurrency_count`, `llm_model_spec`, `generation_mode`, and `graph_expand_top_k`.
- `concurrency_count` is bounded by service constants; use low values when provider rate limits are strict.
- `generation_mode="graph_enhanced"` requires at least one graph-indexed chunk.

Evaluation run notes:

- Run IDs have `run_<8 hex>` form.
- Runtime retrieval config starts from the KB query params and overlays per-run `model_config` fields.
- If `gold_answer` exists, answer scoring needs a judge or answer LLM from config.
- Reported metrics include recall, F1-style retrieval metrics, answer scores, and an overall score when enough inputs exist.

## Document parsing and `read_file` interaction

- Knowledge ingestion uses `parse_document` to convert files to Markdown and stores results in MinIO.
- Agent `read_file` directly supports UTF-8 text and image files. It rejects PDF/Office documents with a message to use `ocr_parse_file` first.
- For image files, a vision-capable model can inspect the image. If the model rejects image input and a read-file image path is available, middleware can request `ocr_parse_file` automatically.
- `ocr_parse_file` writes Markdown under sandbox `outputs/ocr/` and returns only a short preview plus the parsed virtual path; use `read_file` on the parsed Markdown when the result is long.

## Native candidates that prove this area

| Candidate | Command | Requirement | What it proves |
| --- | --- | --- | --- |
| Parser facade | `pytest backend/test/unit/knowledge/test_parser_facade.py` | CPU-safe backend test environment | Parser registry, metadata, facade selection, local conversion, safe credential cache keys |
| OCR config center E2E | `pytest backend/test/e2e/test_ocr_config_center_e2e.py` | API services, Postgres, MinIO, RapidOCR-capable environment | Default OCR configuration drives real attachment parsing |
| `read_file` multimodal E2E | `pytest backend/test/e2e/test_read_file_multimodal_e2e.py` | API services, sandbox provisioner, configured vision/non-vision models or OCR fallback | Image handling, PDF/Office guidance, model rejection to OCR fallback |

Keep service-required tests out of normal CPU verification unless the deployment environment and credentials are explicitly ready.
