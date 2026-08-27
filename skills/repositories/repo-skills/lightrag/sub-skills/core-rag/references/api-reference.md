# Core API Reference

This reference covers embedded Python APIs from the installed `lightrag-hku` distribution. It intentionally avoids provider credentials and service setup; use `../../llm-providers/SKILL.md` and `../../storage-backends/SKILL.md` for those details.

## Imports

```python
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc, wrap_embedding_func_with_attrs
```

Useful provider functions are exposed under `lightrag.llm.*`, but provider-specific setup is outside this sub-skill.

## `LightRAG` Constructor

Current inspected package: `lightrag-hku` import module `lightrag`, version `1.5.4`.

Core constructor shape:

```python
LightRAG(
    working_dir: str = "./rag_storage",
    kv_storage: str = "JsonKVStorage",
    vector_storage: str = "NanoVectorDBStorage",
    graph_storage: str = "NetworkXStorage",
    doc_status_storage: str = "JsonDocStatusStorage",
    workspace: str = "",
    top_k: int = 40,
    chunk_top_k: int = 20,
    max_entity_tokens: int = 6000,
    max_relation_tokens: int = 8000,
    max_total_tokens: int = 30000,
    cosine_threshold: float = 0.2,
    embedding_func: EmbeddingFunc | None = None,
    embedding_batch_num: int = 10,
    embedding_func_max_async: int = 8,
    embedding_cache_config: dict | None = None,
    llm_model_func: callable | None = None,
    llm_model_name: str = "gpt-4o-mini",
    llm_model_max_async: int = 4,
    llm_model_kwargs: dict | None = None,
    rerank_model_func: callable | None = None,
    rerank_model_max_async: int = 4,
    min_rerank_score: float = 0.0,
    vector_db_storage_cls_kwargs: dict | None = None,
    enable_llm_cache: bool = True,
    enable_llm_cache_for_entity_extract: bool = True,
    max_parallel_insert: int = 3,
    addon_params: dict | None = None,
    auto_manage_storages_states: bool = False,
    **other_pipeline_and_runtime_knobs,
)
```

Required in practice:

- `llm_model_func`: async text-generation function used for extraction and answering.
- `embedding_func`: `EmbeddingFunc` object or decorated async embedding function returning a NumPy array shaped by text count and embedding dimension.
- `working_dir`: persistent location for default file-based storages and caches.

Important constructor relationships:

- `top_k`, `chunk_top_k`, `max_entity_tokens`, `max_relation_tokens`, and `max_total_tokens` set instance-level query defaults, while `QueryParam` overrides them per call.
- `embedding_func_max_async`, `llm_model_max_async`, and `rerank_model_max_async` wrap the supplied functions with concurrency/timeout controls.
- `enable_llm_cache` controls query LLM response caching; `enable_llm_cache_for_entity_extract` controls extraction cache writes.
- `embedding_cache_config` defaults to `{"enabled": False, "similarity_threshold": 0.95, "use_llm_check": False}` and is a separate question-answer embedding cache knob.
- `rerank_model_func` configures reranking globally; `QueryParam(enable_rerank=...)` controls whether a specific query uses it.
- `auto_manage_storages_states` exists for compatibility but embedded code should still explicitly initialize and finalize storages.

## Lifecycle Methods

```python
await rag.initialize_storages()
await rag.finalize_storages()
```

Call `initialize_storages()` once after construction and before all insert/query/custom-KG operations. It creates storage instances, initializes shared pipeline status, and records the event loop used by async locks.

Call `finalize_storages()` during shutdown to flush/finalize storage backends and clean up role LLM queues. Put it in a `finally` block after the `rag` variable may have been assigned.

## Insert APIs

```python
await rag.ainsert(
    input: str | list[str],
    split_by_character: str | None = None,
    split_by_character_only: bool = False,
    ids: str | list[str] | None = None,
    file_paths: str | list[str] | None = None,
    track_id: str | None = None,
) -> str
```

- Returns a `track_id` for monitoring document processing status.
- `ainsert` is a convenience SDK path for raw text and fixed-token chunking.
- `ids` may be one string or a list; when provided, the count must match document count and IDs must be unique.
- `file_paths` may be one string or a list; when provided, the count must match document count. Stored citation paths are canonicalized to document basenames or `unknown_source`.
- `split_by_character` and `split_by_character_only` are fixed-token chunking runtime args. Advanced parser/process-option chunking belongs to `../../document-pipeline/SKILL.md`.

Synchronous wrapper:

```python
rag.insert(...)
```

Use it only in simple synchronous scripts with no running event loop. In async apps, call `await rag.ainsert(...)`.

## Query APIs

```python
await rag.aquery(
    query: str,
    param: QueryParam = QueryParam(),
    system_prompt: str | None = None,
) -> str | AsyncIterator[str]
```

- Non-streaming queries return a string.
- If `QueryParam(stream=True)`, returns an async iterator of string chunks.
- `system_prompt` overrides the default RAG response system prompt for that call.

Structured retrieval without final LLM generation:

```python
await rag.aquery_data(query: str, param: QueryParam = QueryParam()) -> dict
```

Full query result wrapper:

```python
await rag.aquery_llm(query: str, param: QueryParam = QueryParam(), system_prompt: str | None = None) -> dict
```

Synchronous wrappers such as `rag.query(...)` and `rag.query_data(...)` have the same event-loop restrictions as `rag.insert(...)`.

## `QueryParam`

Current inspected signature:

```python
QueryParam(
    mode: Literal["local", "global", "hybrid", "naive", "mix", "bypass"] = "mix",
    only_need_context: bool = False,
    only_need_prompt: bool = False,
    response_type: str = "Multiple Paragraphs",
    stream: bool = False,
    top_k: int = 40,
    chunk_top_k: int = 20,
    max_entity_tokens: int = 6000,
    max_relation_tokens: int = 8000,
    max_total_tokens: int = 30000,
    hl_keywords: list[str] = [],
    ll_keywords: list[str] = [],
    conversation_history: list[dict[str, str]] = [],
    user_prompt: str | None = None,
    enable_rerank: bool = True,
    include_references: bool = False,
)
```

Mode selection:

- `local`: focus on entity-centered context.
- `global`: focus on relationship/global knowledge.
- `hybrid`: combine local and global retrieval.
- `naive`: direct vector retrieval without graph retrieval.
- `mix`: integrate graph and vector retrieval; recommended when reranking is available.
- `bypass`: bypass retrieval and send the prompt directly through the LLM path.

Other fields:

- `only_need_context=True`: return retrieved context without generating an answer.
- `only_need_prompt=True`: return the generated prompt without producing an answer.
- `stream=True`: return an async iterator from `aquery`.
- `conversation_history`: sent to the LLM for conversational context; not used for retrieval ranking.
- `user_prompt`: additional answer instructions injected into the prompt.
- `enable_rerank`: defaults from `RERANK_BY_DEFAULT` when the class is imported; disable per query if no reranker is configured or if latency matters.
- `include_references`: requests reference metadata in supported full-result/API paths; plain `aquery` remains backward-compatible and returns response content.

## Embedding Wrappers

`EmbeddingFunc` signature:

```python
EmbeddingFunc(
    embedding_dim: int,
    func: callable,
    max_token_size: int | None = None,
    send_dimensions: bool = False,
    model_name: str | None = None,
    supports_asymmetric: bool = False,
)
```

`wrap_embedding_func_with_attrs(**kwargs)` decorates an async function and returns an `EmbeddingFunc` instance.

Rules:

- The wrapped function should accept `texts: list[str]` and return a NumPy array with total elements divisible by `embedding_dim`.
- If the underlying function accepts `context`, `wrap_embedding_func_with_attrs` auto-detects asymmetric support unless explicitly set.
- If `send_dimensions=True`, the wrapper injects `embedding_dim` into the underlying function.
- If wrapping a provider function that is already decorated, call its `.func` attribute from your custom wrapper to avoid nested wrapper conflicts.
- `model_name` helps storage backends derive collection/table suffixes for embedding-model isolation when supported.

## Custom KG API

```python
await rag.ainsert_custom_kg(custom_kg: dict[str, Any], full_doc_id: str | None = None) -> None
```

Expected top-level keys:

- `chunks`: list of chunk dicts with required `content` and `source_id`; optional `chunk_order_index` and `file_path`.
- `entities`: list of entity dicts with required `entity_name`; optional `entity_type`, `description`, `source_id`, and `file_path`.
- `relationships`: list of relationship dicts with required `src_id` and `tgt_id`; optional `description`, `keywords`, `weight`, `source_id`, and `file_path`.

Behavior details:

- Chunk `source_id` values are mapped to generated chunk IDs; entity/relation `source_id` should refer to those chunk source IDs.
- Missing chunk mappings become `UNKNOWN` and trigger warnings.
- Duplicate entity names keep the last declaration in a batch.
- Relationships are treated by sorted endpoint pair for deduplication, so the last declaration for an undirected pair wins.
- Missing relationship endpoint nodes are created with `UNKNOWN` metadata.
- Writes are flushed through the normal index-done path.

## `addon_params`

`rag.addon_params` is a live observable mapping. It is normalized at construction and refreshed when LightRAG builds runtime config.

Recognized fields:

- `language`: output language for extraction, summarization, keyword extraction, and multimodal prompts.
- `entity_type_prompt_file`: file name for an entity prompt profile from the configured prompt directory.
- `entity_types_guidance`: inline guidance that overrides prompt-profile and built-in entity guidance.
- `chunker`: nested chunking defaults used for future enqueues.

Precedence highlights:

- Entity guidance precedence: `entity_types_guidance` > `entity_type_prompt_file` profile > built-in defaults.
- Chunking precedence: explicit `addon_params["chunker"]` > strategy-specific `CHUNK_*` environment variables > legacy constructor chunk size fields > legacy environment variables.
- Mutating top-level `addon_params` marks derived prompt state dirty. If you replace the whole mapping, re-read `rag.addon_params` before further edits.
- Nested chunker edits are read for future documents; already-enqueued documents keep their stored chunk-options snapshot.

## Cache And Rerank Knobs

- `enable_llm_cache=True`: enables cache use for query LLM calls.
- `enable_llm_cache_for_entity_extract=True`: enables cache writes for entity extraction calls.
- `await rag.aclear_cache()` or `rag.clear_cache()` clears LLM response cache storage; treat this as a destructive operation.
- `rerank_model_func`: async callable configured on `LightRAG` for reranking retrieved chunks.
- `QueryParam(enable_rerank=True)`: turns reranking on for the query. If no reranker is configured, LightRAG warns and uses original chunks.
- `min_rerank_score`: filters reranked chunks when greater than zero.

## Sync Wrapper Guard

Synchronous wrappers include `insert`, `query`, `query_data`, `insert_custom_kg`, and cache/delete helpers. They drive matching coroutines with an event loop and are convenience APIs for simple scripts only.

They fail fast when:

- Called from inside a running event loop, such as an `async def`, FastAPI handler, notebook cell that already has an active loop, or async test.
- Driven from a different live event loop than the one that initialized storages, such as `loop.run_in_executor(None, rag.insert, ...)`.

Fix both by using the `a*` coroutine from the original async flow.
