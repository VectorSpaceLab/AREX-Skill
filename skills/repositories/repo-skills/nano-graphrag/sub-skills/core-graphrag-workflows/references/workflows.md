# Core GraphRAG workflows

These recipes cover the core lifecycle without relying on source-checkout files. Replace the toy text and fake model/embedding hooks with task-appropriate user data and provider hooks when moving from smoke tests to real operation.

## Minimal import and construction

```python
from nano_graphrag import GraphRAG, QueryParam

rag = GraphRAG(working_dir="./my_graphrag_cache")
```

Important defaults:

- `enable_local=True`, so local search is available by default.
- `enable_naive_rag=False`, so naive search must be opted in before insertion.
- Default LLM and embedding hooks are hosted-provider oriented; use provider-specific guidance before inserting real documents unless the environment already has valid provider configuration.
- Reusing the same `working_dir` reloads default JSON/vector/GraphML artifacts.

## No-network fake embedding and fake LLM pattern

Use this pattern for tests, examples, or smoke checks where no external provider should be called.

```python
import json
import numpy as np
from nano_graphrag import GraphRAG, QueryParam
from nano_graphrag._utils import wrap_embedding_func_with_attrs

@wrap_embedding_func_with_attrs(embedding_dim=8, max_token_size=8192)
async def fake_embedding(texts: list[str]) -> np.ndarray:
    rows = []
    for text in texts:
        # Deterministic, non-random vector; enough for local smoke tests.
        base = (sum(text.encode("utf-8")) % 97) + 1
        rows.append([(base + i) / 100.0 for i in range(8)])
    return np.array(rows, dtype=np.float32)

async def fake_model(prompt, system_prompt=None, history_messages=None, **kwargs) -> str:
    if kwargs.get("response_format") == {"type": "json_object"}:
        return json.dumps({
            "title": "Synthetic report",
            "summary": "Synthetic community summary.",
            "findings": [{"summary": "Finding", "explanation": "Synthetic explanation."}],
            "points": [{"description": "Synthetic support point.", "score": 1}],
        })
    return "Synthetic answer."

rag = GraphRAG(
    working_dir="./safe_cache",
    embedding_func=fake_embedding,
    best_model_func=fake_model,
    cheap_model_func=fake_model,
    enable_naive_rag=True,
)
```

For a complete no-network smoke that also overrides entity extraction, use `scripts/core_smoke.py` from this sub-skill.

## Insert one document

```python
text = "GraphRAG links entities, relationships, source chunks, and community reports."
rag.insert(text)
```

Operational notes:

- The string is stripped before hashing and storage.
- A successful insert chunks text, optionally inserts chunk vectors for naive mode, extracts entities/relationships, clusters the graph, generates community reports, then persists storages.
- If the entity extraction model returns no usable entities, insertion can stop before the full document and chunks are committed; route that symptom to customization troubleshooting.

## Batch insert

```python
rag.insert([
    "Document one text...",
    "Document two text...",
    "Document three text...",
])
```

Batch insertion is useful when all documents should be chunked and indexed in one graph/community-regeneration pass.

## Incremental insert and duplicate behavior

```python
first_half = long_text[: len(long_text) // 2]
second_half = long_text[len(long_text) // 2 :]

rag.insert(first_half)
rag.insert(second_half)
```

What happens internally:

- Full documents are keyed by an MD5 hash of stripped content, so reinserting the identical string is skipped.
- Chunks are keyed by an MD5 hash of chunk content, so repeated chunks are skipped.
- On each non-empty insert, existing community reports are dropped and regenerated because graph communities are recomputed.
- If all docs or chunks already exist, insertion returns early and does not rebuild mode-specific vector indexes. If you need naive mode for an existing cache that was built with `enable_naive_rag=False`, prefer a fresh `working_dir` or a deliberate storage rebuild rather than simply flipping the flag and reinserting the same text.

## Query modes

```python
# Global is the default mode.
answer = rag.query("What themes appear in the documents?")

# Local graph search: requires enable_local=True.
local_answer = rag.query(
    "Which entities are related?",
    param=QueryParam(mode="local"),
)

# Naive chunk search: requires enable_naive_rag=True before insertion.
naive_answer = rag.query(
    "Which source chunk discusses entities?",
    param=QueryParam(mode="naive"),
)
```

Mode selection:

- Use `global` for community-report-oriented answers across the graph.
- Use `local` for entity-centered retrieval with related reports, relationships, and source chunks.
- Use `naive` for direct chunk-vector retrieval without graph-local context.

## Context-only retrieval

Use `only_need_context=True` when another system will do final answer generation or you need to inspect retrieved context.

```python
# Local context-only retrieval. enable_local must be True.
context = rag.query(
    "Show context about Project Alpha.",
    param=QueryParam(mode="local", only_need_context=True, top_k=10),
)

# Naive context-only retrieval. enable_naive_rag must be True and populated.
chunk_context = rag.query(
    "Find raw chunks about Project Alpha.",
    param=QueryParam(mode="naive", only_need_context=True, top_k=5),
)

# Global context-only retrieval returns support points, but the global map step still uses the best model.
global_points = rag.query(
    "Find global support points.",
    param=QueryParam(mode="global", only_need_context=True),
)
```

If a user asks for context-only local retrieval but local mode was disabled, construct or reload with `GraphRAG(..., enable_local=True)` and query with `QueryParam(mode="local", only_need_context=True)`. If the cache was built with local disabled, verify that entity vectors exist or rebuild the cache.

## Persistence and reload

```python
cache_dir = "./project_graph_cache"

rag = GraphRAG(
    working_dir=cache_dir,
    embedding_func=my_embedding,
    best_model_func=my_best_model,
    cheap_model_func=my_cheap_model,
    enable_naive_rag=True,
)
rag.insert(user_texts)

# Later process or later run:
rag2 = GraphRAG(
    working_dir=cache_dir,
    embedding_func=my_embedding,
    best_model_func=my_best_model,
    cheap_model_func=my_cheap_model,
    enable_naive_rag=True,
)
print(rag2.query("What changed?", param=QueryParam(mode="local")))
```

Reload checklist:

- Use the same `working_dir`.
- Keep compatible storage classes.
- Keep compatible embedding dimensions for vector indexes.
- Enable the query modes you intend to use.
- If a query returns fallback output after reload, inspect whether the relevant artifact exists: community reports for global, `vdb_entities.json` for local, and `vdb_chunks.json` for naive when using default storage.

## Async workflow

Every public sync method has an async equivalent prefixed by `a`.

```python
from nano_graphrag import GraphRAG, QueryParam

async def build_and_query(texts: list[str]) -> str:
    rag = GraphRAG(
        working_dir="./async_cache",
        embedding_func=my_embedding,
        best_model_func=my_best_model,
        cheap_model_func=my_cheap_model,
        enable_naive_rag=True,
    )
    await rag.ainsert(texts)
    return await rag.aquery(
        "Summarize the graph.",
        param=QueryParam(mode="global"),
    )
```

Use async methods inside an existing event loop. The sync methods are convenience wrappers and call an event loop internally.

## Token budgets for retrieval

Tune `QueryParam` before changing core code:

```python
param = QueryParam(
    mode="local",
    top_k=30,
    local_max_token_for_text_unit=6000,
    local_max_token_for_local_context=6000,
    local_max_token_for_community_report=4000,
    response_type="Concise bullet list",
)
answer = rag.query("What are the key risks?", param=param)
```

Common knobs:

- `top_k`: number of vector-search results used by local/naive modes.
- `local_max_token_for_text_unit`: source chunk context budget for local mode.
- `local_max_token_for_local_context`: relationship context budget for local mode.
- `local_max_token_for_community_report`: community report budget for local mode.
- `local_community_single_one=True`: restrict local search to one community report after retrieval.
- `global_min_community_rating`: filter global community reports by report rating.
- `global_max_consider_community`: cap communities considered by global search.
- `global_max_token_for_community_report`: budget for global community map/reduce context.
- `response_type`: inserted into response prompts for final answer style.

## Built-in chunking choices

```python
from nano_graphrag._op import chunking_by_token_size, chunking_by_seperators

rag_by_size = GraphRAG(
    working_dir="./chunk_by_size",
    chunk_func=chunking_by_token_size,
    chunk_token_size=1200,
    chunk_overlap_token_size=100,
)

rag_by_separator = GraphRAG(
    working_dir="./chunk_by_separator",
    chunk_func=chunking_by_seperators,  # package spelling
    chunk_token_size=1200,
    chunk_overlap_token_size=100,
)
```

Use `chunking_by_token_size` for straightforward sliding windows. Use `chunking_by_seperators` when preserving prompt-defined text separators is more important.

## Custom chunking validation pattern

Current chunk functions receive a `TokenizerWrapper`, not a raw encoder. Validate the signature and output schema before using it in `GraphRAG`.

```python
from nano_graphrag._op import get_chunks
from nano_graphrag._utils import TokenizerWrapper


def sentenceish_chunks(tokens_list, doc_keys, tokenizer_wrapper, overlap_token_size=0, max_token_size=80):
    results = []
    for doc_index, tokens in enumerate(tokens_list):
        # A tiny demonstrator: split fixed windows but use the current wrapper API.
        step = max(1, max_token_size - overlap_token_size)
        for chunk_index, start in enumerate(range(0, len(tokens), step)):
            piece = tokens[start : start + max_token_size]
            results.append({
                "tokens": len(piece),
                "content": tokenizer_wrapper.decode(piece).strip(),
                "chunk_order_index": chunk_index,
                "full_doc_id": doc_keys[doc_index],
            })
    return results

wrapper = TokenizerWrapper(tokenizer_type="tiktoken", model_name="gpt-4o")
chunks = get_chunks(
    {"doc-demo": {"content": "Alpha sentence. Beta sentence. Gamma sentence."}},
    chunk_func=sentenceish_chunks,
    tokenizer_wrapper=wrapper,
    overlap_token_size=0,
    max_token_size=8,
)

assert chunks
for chunk in chunks.values():
    assert {"tokens", "content", "chunk_order_index", "full_doc_id"} <= set(chunk)

rag = GraphRAG(
    working_dir="./custom_chunk_cache",
    chunk_func=sentenceish_chunks,
    chunk_token_size=80,
    chunk_overlap_token_size=0,
)
```

For stale snippets that name the third parameter `tiktoken_model` or import removed tokenizer helpers, adapt them to `tokenizer_wrapper.encode`, `tokenizer_wrapper.decode`, or `tokenizer_wrapper.decode_batch` before use.
