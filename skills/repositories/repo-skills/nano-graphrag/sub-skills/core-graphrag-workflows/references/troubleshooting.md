# Core workflow troubleshooting

Use this reference for failures around import, construction, insertion, query modes, chunking, tokenizers, context-only retrieval, and persistence. Provider implementation details, storage backend replacement, prompt/entity extraction, and JSON repair belong to sibling sub-skills.

## Import fails: missing `transformers`

Symptom:

```text
ModuleNotFoundError: No module named 'transformers'
```

Cause:

- `nano_graphrag._utils` imports `transformers.AutoTokenizer` at module import time.
- The package metadata may not install `transformers` automatically, even if you only intend to use the default `tiktoken` tokenizer.

Repair:

```bash
python -m pip install transformers
python -c "import nano_graphrag; from nano_graphrag import GraphRAG, QueryParam; print(nano_graphrag.__version__)"
```

If this succeeds, continue with GraphRAG configuration. If it still fails, inspect the active Python environment rather than the GraphRAG workflow.

## Local query fails because local mode is disabled

Symptom:

```text
ValueError: enable_local is False, cannot query in local mode
```

Cause:

- `GraphRAG.aquery` explicitly rejects `QueryParam(mode="local")` when the instance was constructed with `enable_local=False`.

Repair:

```python
rag = GraphRAG(
    working_dir="./cache",
    enable_local=True,
    embedding_func=my_embedding,
    best_model_func=my_best_model,
    cheap_model_func=my_cheap_model,
)
context = rag.query(
    "Give me only the retrieved context.",
    param=QueryParam(mode="local", only_need_context=True),
)
```

Notes:

- `enable_local=True` is the default. This error usually means a caller explicitly disabled local mode or reloaded with different flags.
- Local mode also needs an entity vector index populated during insertion. If the cache was built with local disabled, rebuild or deliberately repopulate the local index.

## Naive query fails because naive mode is disabled

Symptom:

```text
ValueError: enable_naive_rag is False, cannot query in naive mode
```

Cause:

- `enable_naive_rag` defaults to `False`.
- The chunk vector index is only created and populated when `enable_naive_rag=True` during insertion.

Repair:

```python
rag = GraphRAG(
    working_dir="./naive_cache",
    enable_naive_rag=True,
    embedding_func=my_embedding,
    best_model_func=my_best_model,
    cheap_model_func=my_cheap_model,
)
rag.insert(texts)
print(rag.query("Find matching chunks.", param=QueryParam(mode="naive")))
```

If you inserted the same documents earlier with `enable_naive_rag=False`, simply flipping the flag and reinserting identical text can return early because the full docs/chunks already exist. Use a fresh `working_dir` or an intentional vector-index rebuild.

## Unknown query mode

Symptom:

```text
ValueError: Unknown mode hybrid
```

Cause:

- `QueryParam.mode` supports exactly `"global"`, `"local"`, and `"naive"`.

Repair:

```python
param = QueryParam(mode="global")  # or "local" or "naive"
```

Do not invent modes such as `hybrid`, `mix`, or `context`. Use `only_need_context=True` as a flag on a supported mode.

## Context-only local query with local disabled

User intent:

> "I only need local retrieval context, not a final model answer."

Correct core setup:

```python
rag = GraphRAG(
    working_dir="./cache",
    enable_local=True,
    embedding_func=my_embedding,
    best_model_func=my_best_model,
    cheap_model_func=my_cheap_model,
)
context = rag.query(
    "Question needing graph-local context",
    param=QueryParam(mode="local", only_need_context=True),
)
```

Why this matters:

- `only_need_context=True` skips final response generation for local mode, but it does not bypass the `enable_local` guard.
- Local retrieval still needs the entity vector index and graph/community artifacts from insertion.

## Empty graph, no entities, or Leiden/community errors

Symptoms may include:

- Insertion logs or progress showing zero extracted entities/relationships.
- Warning similar to "No new entities found" or "Didn't extract any entities".
- Graph clustering failures from Leiden/graspologic on an empty graph, sometimes reported as an empty network error.
- Global queries returning the package fail response because no community schema or reports exist.

Core interpretation:

- This is usually an entity-extraction/model-output problem, not a query-mode problem.
- The default insert pipeline needs entity/relation records before graph clustering and community report generation can succeed.

Immediate checks:

1. Confirm the document text is non-empty after stripping.
2. Confirm the best model function actually returns entity-extraction output in the expected prompt format.
3. Confirm provider functions do not drop required kwargs or return malformed/empty content.
4. Confirm the token/context window is large enough for the extraction prompt and chunk.

Route detailed fixes to `customization-and-troubleshooting`, especially for prompt formats, `PROMPTS`, JSON repair, DSPy/custom entity extraction, and Ollama/local-model context issues.

## Chunk function signature mismatch

Symptoms:

```text
TypeError: my_chunk_func() got an unexpected keyword argument 'tokenizer_wrapper'
TypeError: my_chunk_func() got an unexpected keyword argument 'doc_keys'
AttributeError: 'TokenizerWrapper' object has no attribute 'decode_batch'  # if using a stale wrapper or wrong object
KeyError: 'content'
KeyError: 'full_doc_id'
```

Current contract:

```python
def my_chunk_func(tokens_list, doc_keys, tokenizer_wrapper, overlap_token_size=128, max_token_size=1024):
    return [
        {
            "tokens": 10,
            "content": "decoded text",
            "chunk_order_index": 0,
            "full_doc_id": doc_keys[0],
        }
    ]
```

Repairs:

- Accept `tokens_list`, `doc_keys`, `tokenizer_wrapper`, `overlap_token_size`, and `max_token_size`.
- Use `tokenizer_wrapper.decode(...)` or `tokenizer_wrapper.decode_batch(...)` to decode tokens.
- Return a list of dictionaries with `tokens`, `content`, `chunk_order_index`, and `full_doc_id`.
- Do not use stale examples that import removed helpers or expect a raw tiktoken model as the third argument.
- Keep `chunk_overlap_token_size < chunk_token_size`; otherwise sliding-window chunkers can produce invalid ranges.

## Tokenizer selection problems

### Unknown tokenizer type

Symptom:

```text
ValueError: Unknown tokenizer_type: ...
```

Repair: use `tokenizer_type="tiktoken"` or `tokenizer_type="huggingface"`.

### HuggingFace tokenizer cannot load

Symptoms can include model-not-found, offline cache, or missing dependency errors.

Repairs:

- Install `transformers` first.
- Use a `huggingface_model_name` that is available in the active environment or cache.
- For safe no-network smoke tests, prefer the default `tokenizer_type="tiktoken"` and `tiktoken_model_name="gpt-4o"`.

### Separator chunking typo

The package function is spelled `chunking_by_seperators`, not `chunking_by_separators`.

```python
from nano_graphrag._op import chunking_by_seperators
```

## Persistence/reload surprises

### Reloading does not show previous data

Checklist:

- Did the new `GraphRAG` use the exact same `working_dir` string/path?
- Were default storage classes changed between insert and reload?
- Did insertion complete successfully through `_insert_done`?
- Do default artifacts exist for the mode you are using?
  - Global: `kv_store_community_reports.json` and `graph_chunk_entity_relation.graphml`.
  - Local: `vdb_entities.json` plus graph/reports/chunks.
  - Naive: `vdb_chunks.json` plus text chunks.

### Reusing a cache with different embedding dimensions

Vector indexes depend on the embedding dimension used when they were created. If you change `embedding_func.embedding_dim`, expect vector storage/query issues and rebuild the cache or index.

### Reusing a cache with different enable flags

The enable flags control which vector indexes are instantiated and populated. Keep `enable_local` and `enable_naive_rag` consistent with the query modes you need, and remember that naive mode is opt-in.

## Global context-only still calls the model

Symptom:

- A user sets `QueryParam(mode="global", only_need_context=True)` but still sees best-model calls.

Cause:

- Global mode first maps community reports into support points using the best model. `only_need_context=True` returns those support points before final reduce-answer generation, but it does not skip the global map step.

Alternative:

- If the user needs no final answer generation and no global-map model call, use local or naive context retrieval when those modes meet the task need.

## Insert returns early and indexes are not rebuilt

Symptoms:

- Log warning similar to "All docs are already in the storage" or "All chunks are already in the storage".
- A newly enabled mode still has an empty vector index.

Cause:

- `insert` deduplicates docs and chunks by content hash and returns early when nothing new remains.

Repairs:

- Use a fresh `working_dir` for a clean rebuild.
- Insert genuinely new content if incremental update is intended.
- For backend-specific manual rebuilds, route to `storage-backends` rather than editing default artifacts ad hoc.

## Safe smoke script fails

Run help first:

```bash
python scripts/core_smoke.py --help
```

If default execution fails:

- Import error for `transformers`: install `transformers`.
- Import error for package dependencies: install the package and its requirements in the active environment.
- Failure during full insert/query smoke but chunk/guard checks passed: inspect entity extraction, graph clustering, and package dependency versions; route empty graph/model-output details to `customization-and-troubleshooting`.
- Failure only when using `--work-dir`: try a fresh empty directory or omit `--work-dir` to use a temporary directory.
