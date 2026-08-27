# Data and RAG troubleshooting

Diagnose from the earliest boundary that fails. Keep the original error, backend,
input identifier, and whether the operation was local or remote.

## Loader and file failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Unsupported knowledge document type` | Factory suffix is not one of the registered `DocumentType` values or parser class is unavailable. | Normalize to a supported suffix or instantiate the concrete class; verify the optional parser extra. Do not rename an invalid binary blindly. |
| `file path is required` | Concrete loader was constructed without a path and no loader object. | Supply a real approved local file path or a tested loader. |
| `UnicodeDecodeError` for CSV | Encoding is not UTF-8 or export is mixed/invalid. | Inspect bytes, choose an explicit encoding, and record it. Do not silently discard undecodable cells in strict mode. |
| TXT content is garbled | `chardet` guessed incorrectly, especially for short text. | Run a bounded encoding probe, compare known header text, then load with an explicit decoding path or report uncertainty. |
| Markdown loses characters | Direct Markdown loading uses UTF-8 with ignored decode errors. | Preflight strict decoding, convert the file, or report possible loss; do not claim byte-perfect ingestion. |
| CSV source column error | `source_column` is absent from the header. | Correct the exact column name or omit `source_column` to use the file path as source. |
| PDF/DOCX/XLSX import or parser error | Optional dependency missing, file malformed, unsupported feature, or extension/content mismatch. | Probe the parser package, use a tiny valid fixture, and classify the file as invalid/blocked. Do not pass raw binary data to a splitter. |
| No documents/chunks from a non-empty file | Parser returned empty content, all spreadsheet rows were blank, or splitter removed blank segments. | Inspect raw `Document.content`, parser metadata, and chunk strategy. Treat zero accepted chunks as a failed input unless explicitly expected. |
| Excel sheets disappear | Sheet has no usable rows/columns or all columns are blank after cleanup. | Inspect sheet dimensions and header detection. Numeric-only sheets use fallback numeric headers; empty sheets are intentionally skipped. |

## Chunking failures

- **`ValueError` about overlap larger than size**: enforce
  `0 <= chunk_overlap < chunk_size`. For a no-overlap diagnostic use zero.
- **Invalid strategy error**: use the concrete knowledge class's supported
  strategies. Markdown supports header, size, and separator; a strategy valid
  for Markdown is not automatically valid for CSV or a datasource.
- **Oversized chunks despite a target**: a long atomic segment can exceed the
  target and is logged as a warning. Choose a separator/recursive splitter or
  accept and record the exception; never silently truncate source text.
- **No overlap observed**: overlap is a target applied while merging split
  segments, not a guarantee across page/paragraph/row boundaries. Validate the
  selected strategy's semantics.
- **Metadata missing after split**: inspect the source `Document.metadata` and
  whether a custom splitter converts objects without preserving metadata. Use
  `split_documents`/`create_documents` with matching metadata lists and test a
  tiny fixture.
- **Duplicate chunks**: repeated source ingestion, unstable ids, or a collection
  upsert/index policy. Choose stable source/document/chunk ids and explicit
  `skip`, `replace`, or `allow` semantics.

## Embedding and vector failures

| Symptom | Recovery |
|---|---|
| `Embeddings is None` or `embedding_fn is required` | Supply the same concrete embedding object to indexing and querying. Provider/model installation is a `models-and-serving` task. |
| Embedding call returns empty/non-numeric values | Stop before persistence; inspect provider response shape and model availability. Do not coerce an invalid vector. |
| Vector dimension mismatch | Probe query/document dimensions and compare with collection metadata/model identity. Reject before `load_document`, `upsert`, collection creation, or network access. Recreate a disposable collection with the correct embedding rather than padding/truncating. |
| Existing Chroma collection returns no hits | Check `persist_path`, normalized collection name, collection count, embedding identity, and whether documents were actually persisted. A collection import does not prove it contains data. |
| Chroma constructor fails on collection name | Use a short stable alphanumeric/underscore name. Let the package normalize only after documenting the effective name. |
| Chroma metadata upsert fails | Chroma metadata must be scalar/serializable. Remove nested objects or encode them intentionally; keep rich metadata outside the vector payload if needed. |
| Search score threshold removes everything | Scores are backend-specific; inspect raw scores, lower the threshold for diagnosis, and verify the query/document embedding path. Do not compare thresholds across stores. |
| Persist intermittently skips chunks | Bounded store loading retries failed groups per chunk and warns. Inspect skipped ids and the first backend error; strict callers should prevalidate and use direct loading only when all-or-nothing is required. |
| Local model download/GPU error | Stop and hand off to `models-and-serving`; CPU package imports do not establish CUDA or model-cache readiness. |

## SQLite and SQLAlchemy failures

- **Cannot open path**: use an approved writable directory; parent creation is
  supported by `from_file_path`, but permissions and path policy still apply.
- **`:memory:` database appears empty on another connection**: each SQLite
  in-memory connection can be isolated. Reuse one connector/engine or use a
  temporary file for multi-thread or multi-step checks.
- **Thread errors**: `check_same_thread=False` is the DB-GPT default, but it does
  not make arbitrary concurrent writes safe. Bound worker threads and use a
  transaction-aware connector.
- **Schema introspection returns no tables**: commit fixture DDL, ensure the
  connector has synchronized metadata, and check the actual database path.
- **`get_show_create_table`/PRAGMA errors**: validate table identifiers against
  known fixture or connector table names; do not interpolate untrusted names.
- **SQLAlchemy/driver import errors**: verify the selected connector extra and
  installed package versions. Do not treat SQLite success as proof for MySQL,
  PostgreSQL, or warehouse dialects.
- **Unexpected write**: stop, restore from a disposable fixture, and route
  production SQL/data mutation to the API/client or approved datasource
  workflow. Schema RAG should not execute arbitrary user SQL.

## Elasticsearch/BM25 failures

- **Connection refused/timeout/502**: the service is unavailable, endpoint is
  wrong, or a proxy/controller is not reachable. This is not a chunking failure;
  verify service readiness with an approved read-only check.
- **Authentication/SSL error**: use secret management and explicit TLS options;
  never place credentials in the skill or logs.
- **Index exists with incompatible mapping**: use a unique test index or perform
  an explicit migration/rebuild. Do not assume an existing index matches current
  chunk metadata or BM25 settings.
- **No lexical hits**: inspect analyzed terms, exact spelling, index refresh,
  top-k, and score threshold. BM25 is lexical; use embeddings for semantic
  paraphrases.
- **Cleanup fails**: report the index name and deletion status. Do not retry
  destructive deletion indefinitely without confirmation.

## Graph RAG failures

- **Graph adapter import fails**: install/enable the adapter extra through the
  environment owner; no graph-service claim can be made from core imports.
- **Graph service unavailable/auth failure**: verify host, port, graph name,
  credentials, and service version with explicit permission. Keep local chunk
  and parser checks separate.
- **Triplets/communities are empty**: LLM extraction, embedding, graph family
  flags, or batch limits may be disabled. Inspect extraction logs and model
  readiness; do not infer graph completeness from a document graph alone.
- **Text2GQL returns empty results**: ensure the feature/model is enabled and
  the generated query matches the graph schema. A retriever cannot return edges
  that were never built.
- **Call-chain/inheritance query is empty**: the current code graph may emit
  `contains`/`defines` but not every possible call/inheritance edge. Report the
  graph builder's actual edge set.
- **Graph delete/truncate failure**: stop and preserve the graph identity for
  manual cleanup; graph deletion is external destructive state.

## Duplicate knowledge and recovery policy

Low-level vector upsert, full-text indexing, and API knowledge-space upload are
different duplicate layers. When a duplicate appears:

1. compare normalized source id/path and content hash;
2. check existing chunk ids/collection/index identity;
3. choose `skip`, `replace`, or `allow` explicitly;
4. record the decision and any cleanup;
5. route live knowledge-space CRUD/status to `apis-client-and-sandbox`.

For a mixed valid/invalid batch, deterministic partial success is acceptable only
when requested: emit `accepted`, `skipped`, and `failed` records and never hide
a skipped file. If all inputs fail, return a failed run with the first and
aggregate reasons. Keep unknown parser/backend behavior explicit rather than
inventing a fallback.
