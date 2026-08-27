---
name: package-extensions
description: "Build and diagnose GraphRAG lower-level package extensions: custom
  caches, storage and table providers, input readers, chunkers, vector stores
  and filters, LLM completion/embedding providers, tokenizers,
  metrics/retry/rate-limit/template factories, graph helpers, and indexing
  workflow factories."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# GraphRAG Package Extensions

Use this sub-skill when the task mentions custom providers, factory registration, extension points, offline mocks, graph helper validation, vector-store filters, timestamp/date fields, chunkers, or low-level package diagnostics.

For user-facing YAML/config selection, route to `../configuration-data/`. For indexing orchestration or running pipelines, route to `../indexing/`. For query APIs and result-table requirements, route to `../querying/`.

## Core Pattern

GraphRAG package extensions usually follow the same pattern:

1. Implement the package interface or subclass the base class.
2. Register it under a stable string key with the package `register_*` function.
3. Use the matching config model or `create_*` helper so GraphRAG instantiates it.
4. Keep optional services behind explicit dependency and credential checks.

The shared factory base supports `scope="transient"` and `scope="singleton"`. `create()` removes init args whose value is `None`, so use a sentinel or explicit default if an initializer must distinguish "unset" from `None`. Singleton instances are cached by strategy plus init args; avoid singleton scope for mutable per-run state unless the init args fully identify the state.

## Common Extension Points

- **Cache**: implement `graphrag_cache.Cache`, register with `register_cache(type, initializer, scope="transient")`, create with `create_cache(CacheConfig(...), storage=...)`.
- **Storage**: implement `graphrag_storage.Storage`, register with `register_storage(type, initializer)`, create with `create_storage(StorageConfig(...))`.
- **Table provider**: implement `graphrag_storage.tables.TableProvider`, register with `register_table_provider(type, initializer)`, create with `create_table_provider(TableProviderConfig(...), storage=...)`.
- **Input reader**: subclass or implement `graphrag_input.InputReader`, register with `register_input_reader(type, initializer)`, create with `create_input_reader(InputConfig(...), storage)`.
- **Chunker**: implement `graphrag_chunking.Chunker`, register with `register_chunker(type, initializer)`, create with `create_chunker(ChunkingConfig(...), encode=..., decode=...)`.
- **Vector store**: subclass `graphrag_vectors.VectorStore`, register with `register_vector_store(type, initializer)`, create with `create_vector_store(VectorStoreConfig(...), IndexSchema(...))`.
- **LLM providers**: implement completion or embedding interfaces, register with `register_completion` or `register_embedding`; model config `model_extra` fields are passed through to initializers.
- **LLM utilities**: tokenizer, retry, rate-limit, metrics store/processor/writer, template manager/engine factories have analogous `register_*` and `create_*` helpers.
- **Index workflows**: register workflow callables with `PipelineFactory.register(name, workflow)` and methods with `PipelineFactory.register_pipeline(name, [workflow_names...])`.
- **Graph helpers**: use deterministic DataFrame helpers such as `compute_degree`, `connected_components`, `largest_connected_component`, and `stable_lcc` for offline graph checks.

## Recommended Workflow

1. Identify the package boundary first: storage/cache/input/chunking/vector/LLM/graph/workflow.
2. Inspect the initializer signature of the target base or built-in implementation.
3. Decide factory scope: transient for fresh state, singleton only for shareable clients keyed by complete init args.
4. Register a unique key before calling `create_*`; duplicate keys overwrite the previous initializer in the process.
5. Create a tiny offline mock before adding optional cloud/database dependencies.
6. Add a smoke check for `--help`, factory registration, and one deterministic operation.
7. If wiring through GraphRAG config, move user-facing config guidance to `../configuration-data/`.

## Bundled Scripts

- `scripts/register_mock_extensions.py` demonstrates offline custom storage, cache, input reader, vector store, and direct factory patterns.
- `scripts/validate_graph_helpers.py` checks degree, connected components, stable LCC normalization/order, timestamp explosion, and filter expressions on deterministic in-memory data.

Both scripts are examples for future agents to copy or adapt inside their own workspace. They do not require external services.

## References

- `references/factory-extension-recipes.md` for concrete registration recipes and design notes.
- `references/package-optional-dependencies.md` for guarded dependency and service guidance.
- `references/troubleshooting.md` for factory, config, service, vector filter, and graph-helper failures.
