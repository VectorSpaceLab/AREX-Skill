# Embedded Workflows

These recipes are safe patterns for future agents to adapt in their own project code. Replace placeholder LLM/embedding functions with provider functions from the target environment; provider credentials and service-specific options belong to `../../llm-providers/SKILL.md`.

## Minimal Async Skeleton

```python
import asyncio
from pathlib import Path

from lightrag import LightRAG, QueryParam

WORKING_DIR = Path("rag_storage")

async def main():
    rag = None
    try:
        rag = LightRAG(
            working_dir=str(WORKING_DIR),
            llm_model_func=llm_model_func,
            embedding_func=embedding_func,
        )
        await rag.initialize_storages()

        await rag.ainsert(
            "LightRAG combines graph retrieval with vector retrieval.",
            ids="intro-doc",
            file_paths="intro.txt",
        )
        answer = await rag.aquery(
            "What does LightRAG combine?",
            param=QueryParam(mode="mix", enable_rerank=False),
        )
        print(answer)
    finally:
        if rag is not None:
            await rag.finalize_storages()

asyncio.run(main())
```

Key points:

- Initialize before the first insert/query/custom-KG call.
- Finalize in `finally` so storage buffers and queues are closed even if insert/query fails.
- Use async APIs in async code. Reserve sync wrappers for simple scripts that are not already inside an event loop.

## Custom Embedding Function

Use `wrap_embedding_func_with_attrs` for a direct async embedding implementation:

```python
import numpy as np
from lightrag.utils import wrap_embedding_func_with_attrs

@wrap_embedding_func_with_attrs(
    embedding_dim=1536,
    max_token_size=8192,
    model_name="my-embedding-model",
)
async def embedding_func(texts: list[str]) -> np.ndarray:
    vectors = await call_embedding_backend(texts)
    return np.asarray(vectors, dtype=np.float32)
```

If you need to adapt a provider function that is already decorated, call `.func` inside your wrapper:

```python
from lightrag.llm.openai import openai_embed
from lightrag.utils import wrap_embedding_func_with_attrs

@wrap_embedding_func_with_attrs(
    embedding_dim=3072,
    max_token_size=8192,
    model_name="text-embedding-3-large",
)
async def embedding_func(texts: list[str]):
    return await openai_embed.func(texts, model="text-embedding-3-large")
```

Avoid this anti-pattern:

```python
# Wrong: calls an already decorated EmbeddingFunc from inside another wrapper.
return await openai_embed(texts, model="text-embedding-3-large")
```

For asymmetric models, include a `context` parameter or set `supports_asymmetric=True`:

```python
@wrap_embedding_func_with_attrs(embedding_dim=1024, supports_asymmetric=True)
async def embedding_func(texts: list[str], context: str = "document"):
    prefix = "query: " if context == "query" else "passage: "
    return await embed_backend([prefix + text for text in texts])
```

## Insert Text With IDs And File Paths

```python
track_id = await rag.ainsert(
    [
        "Alpha project studies graph retrieval.",
        "Beta project studies vector retrieval.",
    ],
    ids=["alpha", "beta"],
    file_paths=["alpha-notes.md", "beta-notes.md"],
)
```

Rules:

- `ids` count must match document count and IDs must be unique.
- `file_paths` count must match document count when provided.
- `file_paths` are used for citation/source metadata; LightRAG stores canonical basenames, not arbitrary path traversal semantics.
- Duplicate file basenames or duplicate content can be recorded as failed duplicate attempts in document status.

## Query Modes And Context Controls

```python
param = QueryParam(
    mode="mix",
    top_k=60,
    chunk_top_k=20,
    max_entity_tokens=6000,
    max_relation_tokens=8000,
    max_total_tokens=30000,
    response_type="Bullet Points",
    user_prompt="Prefer concise answers with source-aware wording.",
    enable_rerank=False,
)
answer = await rag.aquery("Summarize project differences", param=param)
```

Use these modes:

- `mix` for graph-plus-vector retrieval and the usual default.
- `hybrid` for local/global graph blending.
- `local` for entity-specific context.
- `global` for broad relationship/community context.
- `naive` for vector-only retrieval.
- `bypass` when you intentionally want no retrieval.

Context-only and prompt-only diagnostics:

```python
context = await rag.aquery("What evidence exists?", param=QueryParam(only_need_context=True))
prompt = await rag.aquery("What prompt would be sent?", param=QueryParam(only_need_prompt=True))
```

Streaming:

```python
stream = await rag.aquery("Explain the graph", param=QueryParam(stream=True))
async for chunk in stream:
    print(chunk, end="")
```

## Rerank Usage Pattern

Constructor-level reranker:

```python
rag = LightRAG(
    working_dir="rag_storage",
    llm_model_func=llm_model_func,
    embedding_func=embedding_func,
    rerank_model_func=rerank_model_func,
    min_rerank_score=0.0,
)
await rag.initialize_storages()
```

Per-query control:

```python
with_rerank = QueryParam(mode="mix", chunk_top_k=10, enable_rerank=True)
without_rerank = QueryParam(mode="mix", chunk_top_k=10, enable_rerank=False)
```

If `enable_rerank=True` but no `rerank_model_func` is configured, LightRAG warns and falls back to the original chunk order. Provider-specific reranker functions and credentials belong to `../../llm-providers/SKILL.md`.

## Cache Controls

Typical defaults:

```python
rag = LightRAG(
    working_dir="rag_storage",
    llm_model_func=llm_model_func,
    embedding_func=embedding_func,
    enable_llm_cache=True,
    enable_llm_cache_for_entity_extract=True,
    embedding_cache_config={
        "enabled": False,
        "similarity_threshold": 0.95,
        "use_llm_check": False,
    },
)
```

Guidance:

- Keep LLM cache enabled during development if repeated extraction/query calls are expensive.
- Disable query cache when testing prompt changes that should force fresh LLM output.
- Treat `await rag.aclear_cache()` as destructive; it clears LLM response cache storage.
- Embedding-model changes require vector data rebuild/clear, not just cache clearing.

## Custom KG Insertion

Use custom KG insertion when the application already has trusted entity/relation/chunk data and wants to bypass LLM extraction for that data.

```python
custom_kg = {
    "chunks": [
        {
            "content": "Alice and Bob collaborate on quantum computing.",
            "source_id": "doc-1",
            "chunk_order_index": 0,
            "file_path": "research-note.md",
        }
    ],
    "entities": [
        {
            "entity_name": "Alice",
            "entity_type": "person",
            "description": "Researcher working on quantum computing.",
            "source_id": "doc-1",
            "file_path": "research-note.md",
        },
        {
            "entity_name": "Bob",
            "entity_type": "person",
            "description": "Collaborator on quantum computing research.",
            "source_id": "doc-1",
            "file_path": "research-note.md",
        },
    ],
    "relationships": [
        {
            "src_id": "Alice",
            "tgt_id": "Bob",
            "description": "Alice and Bob collaborate.",
            "keywords": "collaboration research",
            "weight": 1.0,
            "source_id": "doc-1",
            "file_path": "research-note.md",
        }
    ],
}

await rag.ainsert_custom_kg(custom_kg, full_doc_id="doc-1")
```

Custom KG checklist:

- Every chunk needs `content` and `source_id`.
- Entity/relation `source_id` values should match a chunk `source_id`; otherwise graph/vector metadata gets `UNKNOWN` source mapping warnings.
- Use stable entity names. A duplicate `entity_name` in one batch keeps the last declaration.
- Relationship endpoint pairs are deduplicated as undirected sorted pairs, so the last pair declaration wins.
- Custom KG still needs initialized storages and an embedding function because chunks/entities/relations are upserted to vector stores.

## Addon Params

Construction-time customization:

```python
rag = LightRAG(
    working_dir="rag_storage",
    llm_model_func=llm_model_func,
    embedding_func=embedding_func,
    addon_params={
        "language": "English",
        "entity_types_guidance": "- Project: a named software or research initiative",
        "chunker": {
            "chunk_token_size": 1000,
            "fixed_token": {
                "chunk_token_size": 1000,
                "chunk_overlap_token_size": 100,
            },
        },
    },
)
await rag.initialize_storages()
```

Runtime update for future work:

```python
rag.addon_params["language"] = "German"
rag.addon_params["entity_types_guidance"] = "- Dataset: structured research data"
```

If replacing the whole mapping:

```python
rag.addon_params = {"language": "Chinese"}
current = rag.addon_params
```

Re-read `rag.addon_params` after replacement; old references point to the previous observable mapping.

## Sync Script Pattern

For a simple non-async script only:

```python
rag = LightRAG(
    working_dir="rag_storage",
    llm_model_func=llm_model_func,
    embedding_func=embedding_func,
)
try:
    asyncio.run(rag.initialize_storages())
    rag.insert("Text", ids="doc-1")
    print(rag.query("Question?", param=QueryParam(mode="mix")))
finally:
    asyncio.run(rag.finalize_storages())
```

Prefer the fully async skeleton for applications, services, notebooks, and tests. Do not call `rag.insert()` or `rag.query()` from inside an already-running event loop.

## Choosing Another Sub-skill

- Need file uploads, parser engines, `process_options`, multimodal sidecars, scan/delete concurrency, or R/V/P chunker strategy selection? Use `../../document-pipeline/SKILL.md`.
- Need PostgreSQL, Neo4j, Qdrant, Redis, MongoDB, workspace routing, migrations, or vector DB rebuild/cleanup tools? Use `../../storage-backends/SKILL.md`.
- Need OpenAI/Ollama/Azure/Gemini/Bedrock/Anthropic/Voyage/Zhipu bindings, role LLM overrides, reranker provider functions, or VLM setup? Use `../../llm-providers/SKILL.md`.
- Need HTTP routes, `lightrag-server`, auth, WebUI, Docker, or `.env` generation? Use `../../api-server/SKILL.md`.
