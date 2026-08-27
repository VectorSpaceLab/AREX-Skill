# Factory Extension Recipes

GraphRAG packages expose small factories that register callables by string key and later create instances from config dictionaries. Most built-ins are lazy-registered the first time `create_*` sees their built-in enum value.

## Shared Factory Rules

- `register(strategy, initializer, scope="transient")` stores or replaces the initializer for that key.
- `create(strategy, init_args)` raises `ValueError` for unknown keys and includes registered keys in the error message.
- `create()` drops every init arg whose value is `None` before calling the initializer.
- `scope="singleton"` caches by a hash of `strategy` plus non-`None` init args.
- Factory objects are process-level singletons, so registration affects subsequent creates in the same Python process.

Use unique extension keys such as `acme-memory-storage` or `offline-vector-v1`; avoid replacing built-in keys unless intentionally testing compatibility.

## Cache

Implement the async `Cache` protocol: `get`, `set`, `has`, `delete`, `clear`, and `child`. The constructor receives `storage` and config fields as keyword args.

```python
from graphrag_cache import CacheConfig, create_cache, register_cache

register_cache("demo-cache", DemoCache, scope="transient")
cache = create_cache(CacheConfig(type="demo-cache", extra_flag=True))
```

Use transient scope for mutable in-memory caches. Use singleton only when the initializer args fully identify the backing cache namespace.

## Storage

Implement `Storage`: regex `find`, async `get`/`set`/`has`/`delete`/`clear`, `child`, `keys`, and `get_creation_date`. `create_storage(StorageConfig(...))` passes config fields directly to the initializer.

```python
from graphrag_storage import StorageConfig, create_storage, register_storage

register_storage("demo-storage", DemoStorage)
storage = create_storage(StorageConfig(type="demo-storage", base_dir="ignored-in-memory"))
```

Child storage should preserve parent configuration and isolate a namespace/prefix where appropriate.

## Table Providers

Table providers adapt storage to tabular outputs. `create_table_provider(config, storage=...)` passes the storage object for file-backed providers. Cosmos table providers can inherit connection details from an `AzureCosmosStorage` instance, so avoid duplicating credentials in table config when storage already supplies them.

```python
from graphrag_storage.tables import TableProviderConfig, create_table_provider, register_table_provider

register_table_provider("demo-table", DemoTableProvider)
provider = create_table_provider(TableProviderConfig(type="demo-table"), storage=storage)
```

## Input Readers

`InputReader` wraps a `Storage`, file pattern, and encoding, then yields `TextDocument` objects asynchronously. Implement `read_file(path)` and rely on the base iterator to call `storage.find(re.compile(file_pattern))`.

```python
from graphrag_input import InputConfig, create_input_reader, register_input_reader

register_input_reader("demo-input", DemoInputReader)
reader = create_input_reader(InputConfig(type="demo-input", file_pattern=".*\\.txt$"), storage)
```

## Chunkers

A chunker implements `chunk(text, transform=None) -> list[TextChunk]`. `create_chunker` injects optional `encode` and `decode` callables only when they are not `None`.

```python
from graphrag_chunking import ChunkingConfig, create_chunker, register_chunker

register_chunker("demo-chunker", DemoChunker)
chunker = create_chunker(ChunkingConfig(type="demo-chunker", size=200, overlap=20))
```

If a chunker requires tokenizer functions, validate that `encode`/`decode` were actually passed; otherwise `None` values are not forwarded.

## Vector Stores

Subclass `VectorStore` and implement `connect`, `create_index`, `load_documents`, `similarity_search_by_vector`, `search_by_id`, `count`, `remove`, and `update`.

The base class handles:

- `fields` definitions and user-defined fields with type `date`.
- Built-in `create_date`/`update_date` timestamp component fields.
- `_prepare_document()` for inserts and `_prepare_update()` for updates.
- `similarity_search_by_text()` via a supplied text embedder.

```python
from graphrag_vectors import IndexSchema, VectorStoreConfig, create_vector_store, register_vector_store

register_vector_store("offline-vector", OfflineVectorStore)
store = create_vector_store(
    VectorStoreConfig(type="offline-vector", fields={"published_at": "date"}),
    IndexSchema(index_name="demo", vector_size=3),
)
```

For filters, accept a `FilterExpr` and call `filters.evaluate(document)` or compile it to the backend query language. Preserve `select` and `include_vectors` behavior in search results.

## LLM Completion and Embedding Providers

Completion and embedding factories build helper objects before instantiation: tokenizer, rate limiter, retry, metrics store/processor, cache, and cache key creator. `ModelConfig.model_extra` is merged into initializer kwargs, so custom provider knobs can live there.

```python
from graphrag_llm.completion import register_completion
from graphrag_llm.embedding import register_embedding

register_completion("mock-provider", MockCompletion)
register_embedding("mock-provider", MockEmbedding)
```

Use the built-in mock provider for offline tests when possible. Register real providers only after dependency, credential, timeout, retry, and rate-limit behavior is explicit.

## LLM Utility Factories

The same registration pattern exists for:

- `register_tokenizer` / `create_tokenizer`
- `register_rate_limiter` / `create_rate_limiter`
- `register_retry` / `create_retry`
- `register_metrics_store`, `register_metrics_processor`, `register_metrics_writer`
- `register_template_manager`, `register_template_engine`

Singletons are common for tokenizers, template engines, metrics stores, and built-in LiteLLM clients. Prefer transient for tests that mutate counters, queues, or captured calls.

## Workflow Factories

Indexing pipelines use `PipelineFactory`, not the shared `Factory` base.

```python
from graphrag.index.workflows.factory import PipelineFactory

PipelineFactory.register("demo_workflow", demo_workflow)
PipelineFactory.register_pipeline("demo_method", ["load_input_documents", "demo_workflow"])
pipeline = PipelineFactory.create_pipeline(config, method="demo_method")
```

`create_pipeline` uses `config.workflows` when set; otherwise it looks up the method in registered pipelines. Register all workflow names before creating the pipeline or key lookup will fail when constructing the `Pipeline`.

## Graph Helpers

Graph helpers operate on pandas edge-list DataFrames:

- `compute_degree(df)` counts undirected degree after deduplicating reversed edges.
- `connected_components(df)` returns component node sets sorted by descending size.
- `largest_connected_component(df)` returns the largest component as a set.
- `stable_lcc(df)` normalizes node names with HTML unescape, uppercase, strip; filters to the largest component; normalizes edge direction; deduplicates; and sorts for deterministic output.

Use graph helpers to validate custom graph extraction or post-processing without requiring GraphRAG indexing, LLM calls, or external services.
