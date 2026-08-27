# Data and RAG workflows

These recipes are progressively staged so a Researcher can stop at the first
useful verified boundary. They avoid source-checkout assumptions and make
network, credentials, persistent state, and optional parsers explicit.

## Workflow A: local file to inspected chunks

Use for parser, encoding, metadata, and chunking work without embeddings.

1. Create a tiny fixture under a disposable directory: one Markdown or TXT,
   one small CSV, and optionally one valid XLSX/PDF only when its parser extra is
   already available.
2. Check file type, size, encoding, and expected row/page count.
3. Build a `Knowledge` object with `KnowledgeFactory.from_file_path` or the
   concrete class when encoding/source columns matter.
4. Call `knowledge.load()` and inspect every `Document` for non-empty content and
   source metadata.
5. Create `ChunkParameters` with an explicit strategy/size/overlap.
6. Use `knowledge.extract` where supported, or `ChunkManager(knowledge,
   chunk_parameter).split(documents)` for a direct split check.
7. Assert the chunk count, non-empty content, metadata propagation, and observed
   size/overlap. Preserve a warning list for skipped/invalid files.

Example shape:

```python
from dbgpt_ext.rag import ChunkParameters
from dbgpt_ext.rag.knowledge import KnowledgeFactory
from dbgpt_ext.rag.chunk_manager import ChunkManager

knowledge = KnowledgeFactory.from_file_path("notes.md")
documents = knowledge.load()
params = ChunkParameters(
    chunk_strategy="CHUNK_BY_MARKDOWN_HEADER",
    chunk_size=256,
    chunk_overlap=32,
)
chunks = ChunkManager(knowledge, params).split(documents)
assert chunks and all(chunk.content.strip() for chunk in chunks)
```

For a no-package validation, use `scripts/local_rag_smoke.py`. It is useful for
fixture triage but does not emulate all format-specific parser behavior.

## Workflow B: local SQLite schema inspection

Use when the task involves database structure, SQL-safe schema context, or
`DBSchemaAssembler` preparation.

1. Use `SQLiteConnectorParameters(path=":memory:")` or a temporary file.
2. Create only a tiny fixture table with non-sensitive names and values.
3. Call `get_table_names`, `get_fields`, `get_indexes`, `get_show_create_table`,
   and `table_simple_info` to confirm introspection.
4. Build `DatasourceKnowledge(connector, model_dimension=...)` and load summary
   documents if the summary dependencies are installed.
5. For schema RAG, provide a table vector store and optionally a field store to
   `DBSchemaAssembler.load_from_connection`. Supply deterministic embeddings or
   stop at import/signature validation.
6. Persist only to a disposable local collection; retrieve and verify table and
   field metadata. Close the connector and remove the temporary database.

Keep SQL values parameterized and identifiers constrained to fixture-owned names.
A schema retriever is context retrieval, not permission to execute arbitrary SQL;
SQL execution and datasource API operations route elsewhere.

## Workflow C: local semantic vector retrieval

Use when a local embedding function and Chroma extra are available.

1. Prepare a short fixture and explicit `ChunkParameters`.
2. Instantiate a deterministic embedding object for testing, or use the approved
   configured model; do not download a model implicitly.
3. Probe `embed_query("dimension probe")` and document its dimension/model id.
4. Construct `ChromaVectorConfig(persist_path=<disposable-dir>)` and
   `ChromaStore(config, name=<unique-name>, embedding_fn=<same-embedding>)`.
5. Build `EmbeddingAssembler.load_from_knowledge`, call bounded `persist`, and
   verify accepted ids.
6. Retrieve with `as_retriever(top_k=...)` and validate content, metadata, score
   ordering, and threshold behavior.
7. Delete/truncate the collection and remove the disposable path.

Do not construct the store if the embedding is missing. If a collection already
exists, compare dimension and model identity before any upsert. A mismatch is a
preflight failure, not a recoverable query error.

## Workflow D: BM25/full-text retrieval

Use only when Elasticsearch is explicitly available and approved.

1. Parse a redacted `ElasticsearchStoreConfig`; check the service endpoint with a
   read-only health request outside the skill if permitted.
2. Choose a unique index name and explicit `k1`/`b` values.
3. Create `KnowledgeFactory.from_file_path` and `ChunkParameters` locally first.
4. Construct `BM25Assembler.load_from_knowledge`; expect index checks/creation to
   contact Elasticsearch.
5. Persist, retrieve with `retrieve_with_scores(query, threshold)`, inspect
   metadata/score, and delete the test index.
6. Record service version, index name, cleanup result, and skipped provider/model
   calls.

Never claim this workflow passed from a local BM25 algorithm or package import.
The included native BM25 example is service-bound; use the offline helper for a
safe lexical fixture instead.

## Workflow E: graph RAG

Use only with explicit graph service, embedding, and model/LLM readiness.

1. Choose the graph family: triplets, document structure, Markdown headings,
   code graph, or a deliberate combination.
2. Verify graph adapter import and redacted configuration without connecting.
3. Confirm the LLM and embedding provider independently; graph extraction is not
   CPU-only just because the graph adapter imports.
4. Chunk local documents first and preserve source/chunk metadata.
5. Build/persist graph data with a unique graph/collection name.
6. Retrieve with graph/vector/keyword strategy and inspect traversal/citations.
7. Delete graph/vector state after the test and report any unverified graph
   families.

Graph retrieval can expose only edges that the chosen builder emits. Do not
promise call-chain or inheritance answers solely from a code graph unless those
edge types were actually produced.

## Configuration checklist

For a TOML/env configuration, validate in this order:

- `[rag]`: chunk size/overlap, top-k, score threshold, rewrite, batch limits,
  rerank top-k;
- `[rag.storage.vector]`: backend type, local persistence or remote endpoint,
  collection identity;
- `[rag.storage.full_text]`: Elasticsearch/OpenSearch type and endpoint when
  BM25 is selected;
- `[rag.storage.graph]`: adapter, host/port, graph identity, enabled graph
  families, and secret references;
- `[models.embeddings]`: provider/model/API URL or local model identity, owned by
  `models-and-serving`.

For a local check, remove or replace all remote sections and use a disposable
SQLite/Chroma path. Configuration parsing is not backend readiness.

## Acceptance record

For each run, record:

```text
input files and hashes:
accepted/skipped/invalid files:
loader and encoding:
chunk strategy, size, overlap, observed bounds:
embedding model and dimension:
store/collection/index identity:
persisted and skipped chunk ids:
retrieval query, top-k, threshold, filters:
local/import-only vs external-service checks:
cleanup result:
known omissions:
```
