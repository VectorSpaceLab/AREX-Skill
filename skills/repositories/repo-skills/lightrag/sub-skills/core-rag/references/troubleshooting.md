# Core Troubleshooting

Use this guide for embedded Python `LightRAG` failures. For provider credentials/service failures, storage backend service failures, parser/process-option failures, or API server route failures, route to the sibling sub-skills named in `SKILL.md`.

## Install Or Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'lightrag'`
- Unexpected package version or missing classes.
- Import succeeds in one shell but fails in another.

Checks:

```bash
python skills/lightrag/sub-skills/core-rag/scripts/check_core_api.py
python skills/lightrag/sub-skills/core-rag/scripts/check_core_api.py --json
```

Fixes:

- Ensure the environment has the `lightrag-hku` distribution installed and imports module `lightrag`.
- Verify the script reports `LightRAG`, `QueryParam`, `EmbeddingFunc`, and `wrap_embedding_func_with_attrs`.
- If a project has a local file or directory named `lightrag.py` or `lightrag/`, run from a different working directory or fix the shadowing.
- Do not hard-code local Python executable paths in reusable code; use the active project environment.

## Missing Initialization

Symptoms:

- `AttributeError: __aenter__`
- `KeyError: 'history_messages'`
- Storage attributes missing or not initialized.
- Insert/query/custom-KG operation fails immediately after construction.

Cause:

`LightRAG(...)` constructs the object and storage wrappers, but embedded code must explicitly initialize storages.

Fix:

```python
rag = LightRAG(
    working_dir="rag_storage",
    llm_model_func=llm_model_func,
    embedding_func=embedding_func,
)
await rag.initialize_storages()
try:
    await rag.ainsert("Text")
finally:
    await rag.finalize_storages()
```

Do not rely on `auto_manage_storages_states`; keep explicit lifecycle calls in application code.

## Cleanup Ordering

Symptoms:

- Buffered data not persisted after exceptions.
- Event-loop or queue cleanup warnings at shutdown.
- Tests pass individually but leak state across async tests.

Fix pattern:

```python
rag = None
try:
    rag = LightRAG(...)
    await rag.initialize_storages()
    await rag.ainsert("Text")
    result = await rag.aquery("Question")
finally:
    if rag is not None:
        await rag.finalize_storages()
```

Only finalize after successful construction. Keep finalization on the same async ownership path that initialized the instance when possible.

## Sync Wrapper Misuse In Async Code

Symptoms:

- `insert() cannot be called from within a running asyncio event loop`
- `query() cannot be called from within a running asyncio event loop`
- Error says the sync wrapper must run on the same event loop the instance was initialized on.
- Misuse appears inside FastAPI handlers, notebooks, async tests, or `run_in_executor` calls.

Cause:

Sync wrappers internally drive coroutines with `loop.run_until_complete()`. Python forbids that inside an already running loop, and LightRAG storage locks are bound to the initialization loop.

Fix:

```python
# Wrong inside async code:
rag.insert("Text")
rag.query("Question")

# Right:
await rag.ainsert("Text")
answer = await rag.aquery("Question")
```

For worker threads, route work back to the owning event loop or create, initialize, use, and finalize a separate `LightRAG` instance fully inside that thread's async lifecycle.

## LLM Or Embedding Function Missing

Symptoms:

- `ValueError: llm_model_func must be provided`
- Vector storage reports `embedding_func is required`.
- Insert reaches extraction but fails before provider call.

Fix:

- Pass `llm_model_func` and `embedding_func` to `LightRAG` before `initialize_storages()`.
- Ensure both functions are async-compatible with LightRAG provider expectations.
- Keep provider-specific credentials and host setup in application configuration, not in reusable skill examples.

## Embedding Dimension Or Count Mismatch

Symptoms:

- `Embedding dimension mismatch detected`
- `Vector count mismatch`
- Vector DB rejects records or creates incompatible collections.

Cause:

`EmbeddingFunc` validates that returned NumPy arrays match the declared `embedding_dim` and number of input texts.

Fix:

```python
from lightrag.utils import EmbeddingFunc

embedding_func = EmbeddingFunc(
    embedding_dim=1536,
    max_token_size=8192,
    model_name="my-embedding-model",
    func=my_async_embed,
)
```

Validate the underlying embedding function directly with one or two texts before indexing. If the backend returns a flat vector for one input, convert it to a 2D array shaped `(len(texts), embedding_dim)`.

## Double-Wrapped Embedding Function

Symptoms:

- Warnings about nested `EmbeddingFunc` wrapping.
- Unexpected dimensions or token limits.
- Custom wrapper ignores intended model-specific args.

Cause:

A provider embedding function may already be decorated with `@wrap_embedding_func_with_attrs`. Wrapping it again can cause inner wrapper settings to conflict with outer settings.

Fix:

```python
from lightrag.llm.openai import openai_embed
from lightrag.utils import wrap_embedding_func_with_attrs

@wrap_embedding_func_with_attrs(embedding_dim=3072, max_token_size=8192)
async def embedding_func(texts: list[str]):
    return await openai_embed.func(texts, model="text-embedding-3-large")
```

Use `.func` for the underlying function when adapting an already-decorated provider embedding.

## Embedding Model Switches

Symptoms:

- Retrieval quality collapses after changing embedding model.
- Vector DB dimension errors after switching model.
- New inserts work but old vectors are incompatible or irrelevant.

Cause:

Existing vectors were generated in the old model's vector space or dimension. LLM cache preservation does not make vector data compatible.

Fix:

- Rebuild or clear vector data when changing embedding model, dimension, or asymmetric behavior.
- If using file-based default storage, keep only LLM cache if intentionally preserving cached LLM calls; clear vector and graph/text-chunk data according to the storage-backend guidance.
- For managed/external vector stores, use the storage-backends sub-skill before destructive cleanup.

## Rerank Warning Or No Effect

Symptoms:

- Warning: rerank is enabled but no rerank model is configured.
- `QueryParam(enable_rerank=True)` appears to have no effect.
- Query latency increases unexpectedly.

Cause:

Rerank is controlled by both constructor and query settings:

- `LightRAG(rerank_model_func=...)` supplies the reranker.
- `QueryParam(enable_rerank=True)` asks to use it for that query.

Fixes:

```python
# Disable when no reranker is configured.
param = QueryParam(mode="mix", enable_rerank=False)

# Enable only after constructor-level reranker is supplied.
rag = LightRAG(..., rerank_model_func=rerank_model_func)
param = QueryParam(mode="mix", enable_rerank=True)
```

Provider-specific reranker functions and credentials belong to `../../llm-providers/SKILL.md`.

## Cache Surprises

Symptoms:

- Repeated query returns an old answer after prompt/provider changes.
- Extraction appears not to call the LLM on repeated inputs.
- Streaming responses are not cached.

Facts:

- `enable_llm_cache` controls query LLM cache behavior.
- `enable_llm_cache_for_entity_extract` controls entity-extraction cache writes.
- Cache keys include cache type, prompt inputs, and non-secret model/provider identity.
- Streaming response content is skipped by cache-save logic.

Fixes:

- Temporarily set `enable_llm_cache=False` when testing answer prompt changes.
- Temporarily set `enable_llm_cache_for_entity_extract=False` when forcing fresh extraction behavior.
- Use `await rag.aclear_cache()` only when you intentionally want to clear the LLM response cache.
- Do not confuse LLM cache with vector data compatibility after embedding model changes.

## ID Validation Errors

Symptoms:

- `ValueError: Number of IDs must match the number of documents`
- `ValueError: IDs must be unique`
- Duplicate document records appear in status storage.

Fix:

```python
await rag.ainsert(
    ["Text A", "Text B"],
    ids=["doc-a", "doc-b"],
)
```

Rules:

- For a single document, a single string ID or one-element list is acceptable.
- For a list of documents, pass a list of the same length.
- Ensure IDs are unique within the batch.
- If no IDs are provided, LightRAG derives document IDs from content or file source metadata.

## File Path Validation And Duplicates

Symptoms:

- `ValueError: Number of file paths must match the number of documents`
- A second insert reports duplicate filename or duplicate content.
- Citations show `unknown_source`.

Fix:

```python
await rag.ainsert(
    ["Doc one", "Doc two"],
    file_paths=["one.md", "two.md"],
)
```

Rules:

- `file_paths` count must match document count when provided.
- Empty or placeholder paths become `unknown_source`.
- Stored file paths are canonicalized basenames; two paths with the same effective basename can be treated as filename duplicates.
- Same content under different file paths can be treated as content duplicate.

## Custom KG Source Mapping Warnings

Symptoms:

- Warning that an entity has `UNKNOWN` source mapping.
- Warning that a relationship has `UNKNOWN` source mapping.
- Custom KG inserts but retrieval lacks expected source references.

Cause:

Entity or relationship `source_id` did not match any `source_id` in `custom_kg["chunks"]`.

Fix:

```python
custom_kg = {
    "chunks": [{"content": "Alice works with Bob.", "source_id": "doc-1"}],
    "entities": [{"entity_name": "Alice", "source_id": "doc-1"}],
    "relationships": [{"src_id": "Alice", "tgt_id": "Bob", "source_id": "doc-1"}],
}
await rag.ainsert_custom_kg(custom_kg, full_doc_id="doc-1")
```

Ensure every entity/relation `source_id` references a chunk `source_id` from the same batch.

## Addon Params Not Taking Effect

Symptoms:

- Updated `language` or entity guidance seems ignored.
- Chunker changes affect new documents but not old ones.
- Mutating an old mapping reference after replacement has no effect.

Facts and fixes:

- Top-level `rag.addon_params[...] = ...` marks derived prompt config dirty for later runtime config builds.
- Replacing `rag.addon_params = {...}` creates a new observable mapping; discard old references and re-read `rag.addon_params`.
- Chunker settings are snapshotted at enqueue time; already-enqueued documents keep their prior chunk options.
- Parser/process-option chunking details belong to `../../document-pipeline/SKILL.md`.

## Difficult Diagnostic Cases

Use these as hard usability tests for this sub-skill:

- Given an async app that constructs `LightRAG`, forgets `await initialize_storages()`, calls `rag.insert()` from inside a running event loop, and never finalizes, rewrite it into a correct lifecycle with `await ainsert(...)`, `await aquery(...)`, and `finally: await finalize_storages()`.
- Given a raw OpenAI-compatible embedding wrapper that calls an already-decorated provider function and declares the wrong dimension, convert it into a safe `EmbeddingFunc`/`wrap_embedding_func_with_attrs` implementation using `.func`, correct `embedding_dim`, `model_name`, and a one-text validation probe.
