# RAG Data and Service Formats

## Document/node concepts

Use these concepts when explaining LazyLLM RAG behavior:

- **Source document**: original file, URL, text, or transferred object.
- **DocNode**: chunk/node object with text and metadata; retrieval returns nodes plus scores.
- **Node group**: named group of nodes/chunks used by retrievers and parser-service status tracking.
- **Index/store**: local or external backend used for lexical/vector retrieval.
- **Retriever result**: usually node/score pairs or formatted/joined contexts depending on retriever options.
- **Reranked result**: retrieved contexts reordered by a reranker module.

## File readers and transforms

The `rag` extra includes packages for common formats: PDF, DOCX, PPTX, Excel, HTML, e-book, text, tokenization, and language-specific BM25/tokenizer support. Optional OCR/audio/media readers belong to advanced extras and may require external binaries or models.

When constructing a workflow, record:

- accepted file extensions,
- encoding assumptions,
- chunk size/overlap or transform parameters,
- metadata keys preserved on nodes,
- failure behavior for empty/unreadable files,
- whether remote URLs are allowed.

## Document service request model families

LazyLLM document service tests exercise typed request/status objects for:

- uploads and transfer items,
- add/delete/reparse requests,
- callback requests for task start/finish events,
- knowledge-base and document status values,
- parser-client health and list/chunk APIs,
- local SQLite-backed idempotency and status transitions.

Use these as architectural concepts. For local verification, prefer temporary directories, SQLite, and mocked parser-client methods. For production, require parser URL, DB config, callback URL, storage policy, and service health checks.

## Parser service boundary

Parser service examples distinguish server and worker processes. A safe plan should specify:

- server endpoint and health endpoint,
- worker concurrency/backoff policy,
- document storage location,
- callback URL and retry behavior,
- node-group names and algorithms,
- how failed/working/success document statuses are surfaced.

Do not claim parser service is available from a local package import alone.

## Retrieval output contracts

Before integrating with a model or agent, normalize retrieval output:

- raw `DocNode` objects for downstream Python processing,
- `(node, score)` pairs for ranking/debugging,
- joined strings for prompt context,
- dictionaries with metadata for agent tools or APIs.

Document the chosen contract and test it with a tiny fixture.
