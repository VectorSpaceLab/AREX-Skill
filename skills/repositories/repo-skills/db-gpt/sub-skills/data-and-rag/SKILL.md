---
name: data-and-rag
description: "Use DB-GPT 0.8.1 data and RAG workflows for local documents,
  datasource schema inspection, chunking, embeddings, retrieval, knowledge
  indexing, vector stores, and graph stores; route live knowledge or datasource
  CRUD to the API/client skill and provider setup to model serving."
metadata:
  disco-role: operating
license: Apache 2.0
disable-model-invocation: true
---

# DB-GPT data and RAG

Use this route when the task mentions DB-GPT knowledge spaces, document ingestion,
CSV/Markdown/TXT/PDF/DOCX/XLSX loading, chunk parameters, schema RAG, embeddings,
retrievers, Chroma, BM25/full-text, Milvus, Qdrant, graph RAG, or vector/graph
storage. This skill covers package-level construction and validation for DB-GPT
0.8.1. It does **not** perform live service CRUD or install model/provider
backends.

## Route first

- **Local file or text ingestion**: use [data-formats.md](references/data-formats.md).
- **Chunking, knowledge objects, assemblers, retrievers, and signatures**: use
  [rag-api-reference.md](references/rag-api-reference.md).
- **SQLite or another database, schema introspection, vector/full-text/graph
  backend selection**: use [connectors-and-stores.md](references/connectors-and-stores.md).
- **An end-to-end local-to-index-to-retrieve plan or configuration**: use
  [workflows.md](references/workflows.md).
- **Failures, skipped documents, missing extras, bad embeddings, or remote
  services**: use [troubleshooting.md](references/troubleshooting.md).
- **CRUD of datasource/knowledge spaces, uploads, or chat endpoints**: hand off
  to `apis-client-and-sandbox`; retain only the indexing/storage semantics here.
- **Provider packages, API keys, local model downloads, or serving**: hand off to
  `models-and-serving`.
- **Generic `dbgpt` command routing, profiles, or workspace setup**: hand off to
  `setup-and-cli`.

## Operating contract

Input is one or more local documents, a `Knowledge` object, or a configured
`BaseConnector`, plus an explicit index/retrieval strategy. Output is a
validated list of documents/chunks, a persisted index/assembler, or retrieved
`Chunk` objects with content, metadata, ids, and optionally scores. Keep the
following invariant visible:

```
source -> loader -> Document -> ChunkManager -> index store -> retriever -> context
```

Indexing and conversation are separate. Do not imply that retrieval re-indexes
source files. Preserve source metadata (`source`, row/page/sheet identifiers,
headers, and stable document/chunk ids) so downstream answers can be traced.

## Standard workflow

1. **Classify the input and trust boundary.** Prefer a local, tiny fixture for
   parser or splitter checks. Treat URLs, uploaded files, databases, vector
   services, graph services, and provider calls as external state. Do not fetch
   a URL or connect to a service unless the user explicitly supplied a safe
   endpoint and permission.
2. **Select the loader.** `KnowledgeFactory.create(datasource=..., knowledge_type=...)`
   or `KnowledgeFactory.from_file_path(...)` dispatches document extensions;
   `KnowledgeFactory.from_text(...)` is deterministic and local. Use the
   concrete knowledge class when encoding, source columns, or loader behavior
   must be controlled.
3. **Load and inspect before indexing.** Check file existence, readable encoding,
   non-empty content, document count, metadata, and parser-specific warnings.
   Reject an empty input or record a deterministic skip rather than persisting
   an empty vector. For a mixed directory, process each file independently and
   report skipped files with reasons.
4. **Choose chunking deliberately.** Start with `ChunkParameters()` (size 512,
   overlap 50) only when its defaults fit the input. Select a supported
   `chunk_strategy`: `CHUNK_BY_SIZE`, `CHUNK_BY_PAGE`,
   `CHUNK_BY_PARAGRAPH`, `CHUNK_BY_SEPARATOR`, or
   `CHUNK_BY_MARKDOWN_HEADER`. Ensure `chunk_overlap < chunk_size`; use zero
   overlap for independent rows/pages and positive overlap for prose continuity.
5. **Build the assembler.** Use `EmbeddingAssembler` with an `IndexStoreBase`
   for semantic retrieval, `BM25Assembler` only with an explicitly reachable
   Elasticsearch service, or `DBSchemaAssembler` for database schema chunks.
   Pass an embedding function explicitly for vector stores; do not silently
   substitute a remote/provider model.
6. **Persist and retrieve.** Prefer bounded batches through
   `assembler.persist(max_chunks_once_load=..., max_threads=...)` or the
   assembler's async equivalent. Call `as_retriever(top_k=...)`, then
   `retrieve`, `retrieve_with_scores`, `aretrieve`, or
   `aretrieve_with_scores`. Record the score threshold and filters used.
7. **Validate the result.** Confirm all accepted chunks have non-empty content,
   source metadata, unique ids, and the expected chunk bounds/overlap. For a
   vector store, probe the embedding dimension before the first network or
   persistent write and fail early on a mismatch. For schema RAG, verify table
   and field metadata and that the final retrieved content is usable SQL/schema
   context.
8. **Report boundaries.** State which checks were local/import-only, which
   backend was actually exercised, and which GPU, provider, database, vector,
   or graph service was skipped.

## API and configuration anchors

- `ChunkParameters` is a Pydantic model with `chunk_strategy=None`,
  `text_splitter=None`, `splitter_type=SplitterType.USER_DEFINE`,
  `chunk_size=512`, `chunk_overlap=50`, `separator="\n"`, and
  `enable_merge=None`.
- `KnowledgeFactory.create` accepts `datasource`, `knowledge_type`, and optional
  metadata. Supported factory modes include `DOCUMENT`, `URL`, and `TEXT`;
  URL loading is network-bound and is not a local parser smoke test.
- `SQLiteConnectorParameters(path, check_same_thread=False, driver="sqlite")`
  uses a required path; `:memory:` is valid. `SQLiteConnector.from_parameters`
  and `SQLiteConnector.from_file_path` create SQLAlchemy-backed connectors.
- `EmbeddingAssembler.load_from_knowledge` requires `knowledge` and
  `index_store`; it optionally accepts chunk parameters, `embedding_model`,
  `embeddings`, and a `RetrieverStrategy`. `as_retriever(top_k=4)` returns an
  embedding retriever by default.
- `BM25Assembler.load_from_knowledge` requires `knowledge` and an
  `ElasticsearchStoreConfig`; its defaults are index name `dbgpt`, `k1=2.0`,
  and `b=0.75`. Construction and persistence contact Elasticsearch.
- `DBSchemaAssembler.load_from_connection` requires a connector and table vector
  store, optionally a field vector store, chunk parameters, embedding settings,
  and `max_seq_length=512`.
- `ChromaVectorConfig` accepts `persist_path`, `collection_metadata`, user and
  password fields, and load concurrency fields. `ChromaStore` requires a
  `ChromaVectorConfig`, collection `name`, and a non-null embedding function;
  Chroma is local/persistent when configured with a local path, but it still
  writes state and must use a disposable test directory for checks.
- RAG configuration commonly controls `chunk_size`, `chunk_overlap`,
  `similarity_top_k`, `similarity_score_threshold`, `query_rewrite`,
  `max_chunks_once_load`, `max_threads`, and `rerank_top_k`. Graph settings
  add extraction, similarity, community, and graph-search controls. Keep
  secrets in environment/config management, never in a skill example.

## Validation shortcut

For an offline smoke that does not import DB-GPT or contact Elasticsearch,
Chroma, an embedding provider, or a graph service, run the bundled helper:

```bash
python scripts/local_rag_smoke.py --help
python scripts/local_rag_smoke.py --fixture-dir ./tiny-rag-fixture --chunk-size 32 --chunk-overlap 4
```

The helper creates no files unless `--fixture-dir` is supplied, uses only the
Python standard library, reports deterministic skips for unsupported or invalid
files, chunks local text/Markdown/CSV, and can inspect a SQLite schema. It is a
fixture validator, not a substitute for DB-GPT's loader or backend behavior.

## Quality and safety gates

- Never treat a successful import as proof that a parser, embedding model, vector
  index, or graph service works.
- Never use the original checkout, source-relative examples, private paths, or
  credentials as runtime dependencies.
- Do not send malformed/empty documents to a remote index. Make invalid-file
  handling explicit: skip with a warning for batch ingestion, or fail fast when
  the caller requested strict all-or-nothing behavior.
- Do not reuse a vector collection across embedding models without checking its
  dimension and model identity. A dimension mismatch must be rejected before
  network/persistent writes.
- Do not claim BM25, Milvus, Qdrant, Elasticsearch, TuGraph, Neo4j, Memgraph,
  MySQL, or provider coverage from CPU-only local tests. The confirmed baseline
  is CPU plus local file/SQLite behavior; external services are optional.
- Knowledge-space creation, document upload/delete, datasource CRUD, and chat are
  service/API operations. Route them to the API/client sub-skill and preserve
  deletion/duplicate semantics there.
