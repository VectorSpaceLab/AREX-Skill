# Package Optional Dependencies

GraphRAG lower-level packages support both offline primitives and optional service-backed implementations. Keep optional dependencies guarded: import them only when the selected provider needs them, show a clear install/configuration error, and provide an offline mock path for tests.

## Safe Defaults

- Prefer memory, file, mock, and deterministic in-process implementations for examples and tests.
- Avoid importing cloud/database SDKs at module import time for custom providers.
- Validate credentials and service endpoints before creating clients.
- Make retry, timeout, and rate-limit behavior explicit for network providers.
- Keep user-facing YAML/config selection in `../configuration-data/`; this sub-skill should explain extension mechanics only.

## Storage and Cache

Built-in storage can be local/file, memory, Azure Blob, or Azure Cosmos depending on installed extras and configuration. Cache can be memory, JSON-over-storage, or noop.

Guarded service notes:

- Azure Blob storage requires a valid account/container credential path and network access.
- Azure Cosmos storage and table providers require database/container setup and credentials.
- JSON cache depends on a working `Storage` implementation; pass storage explicitly if config does not define one.
- Cosmos table provider can inherit connection details from an `AzureCosmosStorage` instance.

For offline tests, use memory storage/cache or a custom in-memory implementation.

## Input Readers

Common readers cover text, CSV, JSON, JSON Lines, Parquet, and MarkItDown-backed document conversion. Optional dependency considerations:

- Parquet readers require pyarrow-compatible support.
- MarkItDown readers require MarkItDown and any format-specific dependencies for PDFs, Office files, or other converted formats.
- File discovery uses a regex pattern against storage keys; empty matches produce warnings rather than documents.

For custom readers, start from `InputReader` and implement only `read_file(path)`.

## Chunking

Token chunking is generally offline. Sentence chunking can depend on tokenizer data or NLP packages depending on strategy and environment.

Guarded dependency notes:

- NLTK data may need bootstrapping before sentence splitting in fresh environments.
- spaCy-based workflows require the package and the selected model to be installed.
- Custom chunkers should accept `encode`/`decode` only when needed and fail clearly if tokenization is required but missing.

## Vector Stores

Built-in vector stores include LanceDB, Azure AI Search, and Cosmos DB. These are optional service or package integrations.

Guarded dependency notes:

- LanceDB requires the lancedb package and a reachable local or remote database path.
- Azure AI Search requires endpoint/index credentials and a schema compatible with GraphRAG fields.
- Cosmos DB vector storage requires account/database/container setup and compatible vector indexing support.
- Date fields declared as `fields={"name": "date"}` are stored as strings and expanded into filterable components.
- All stores should handle `FilterExpr`, `select`, and `include_vectors` consistently.

For offline tests, build an in-memory `VectorStore` that calls `_prepare_document()` and evaluates filters with `filters.evaluate(document)`.

## LLM Providers and Utilities

GraphRAG LLM factories compose completion/embedding providers with tokenizers, cache, retry, rate limiters, and metrics.

Guarded dependency notes:

- LiteLLM-backed providers need provider-specific packages or reachable APIs, depending on model/provider.
- Mock completion and embedding providers are preferred for offline tests.
- Tokenizers may require LiteLLM or tiktoken support for the requested model.
- Metrics file writers need a writable destination; log writers need logger configuration.
- Template engines use Jinja by default and can depend on template paths being resolvable.

Keep API keys and endpoints out of public skill content and examples. Show placeholders only when necessary, and prefer runtime environment variables over hard-coded values.

## Graph and Workflow Helpers

Graph helper functions run offline with pandas. Optional graph algorithms such as hierarchical Leiden can require graph-processing packages like graspologic. Use degree, connected-components, and stable-LCC helpers when you need deterministic checks without optional clustering dependencies.

Workflow factory registration itself is offline, but individual workflows may call LLMs, storage, vector stores, or NLP components. Validate each workflow dependency separately.
