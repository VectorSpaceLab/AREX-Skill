# In-Memory Store Reference

LangGraph stores provide long-term key-value memory that is separate from checkpoints. Checkpoints persist graph execution state by thread; stores persist application memory that can be shared across threads, users, or workflows depending on namespace design.

## When To Use A Store

Use a store when the graph needs to remember facts, preferences, summaries, documents, or other application data outside one checkpoint thread.

Examples:

- User profile preferences: namespace `("users", user_id)` and key `"prefs"`.
- Retrieved document snippets: namespace `("docs", collection_id)` and key per document.
- Cross-thread memory: namespace by user rather than by thread.
- Test or prototype semantic memory before moving to a durable/vector backend.

Use a checkpointer instead when the graph only needs to resume its own execution state for a given `thread_id`.

## Basic InMemoryStore

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
store.put(("users", "123"), "prefs", {"theme": "dark", "tier": "pro"})
item = store.get(("users", "123"), "prefs")

assert item.value["theme"] == "dark"
```

Constructor:

```python
InMemoryStore(*, index=None)
```

The store is process-local and is lost when the process exits. Treat it as a development, test, or demo implementation unless the app explicitly accepts ephemeral memory.

## Namespaces And Items

Namespaces are tuples of strings:

```python
("users", "123")
("documents", "product-guides")
("cache", "embeddings", "v1")
```

Each item has:

- `namespace`: tuple path where the item lives.
- `key`: unique key within that namespace.
- `value`: dictionary payload; top-level keys are filterable.
- `created_at` and `updated_at`: timestamps.

Design namespaces around access patterns. If agents need user-wide memory across conversations, use a user namespace rather than a thread namespace.

## Search And Filters

Structured search:

```python
store.put(("docs",), "a", {"kind": "guide", "score": 5, "text": "SQLite setup"})
store.put(("docs",), "b", {"kind": "note", "score": 2, "text": "temporary"})

results = store.search(("docs",), filter={"kind": "guide"}, limit=10)
```

Comparison operators supported by store search filters include:

```python
{"score": {"$gt": 4}}
{"score": {"$gte": 3}}
{"status": {"$ne": "archived"}}
{"age": {"$lt": 30}}
{"age": {"$lte": 30}}
```

Pagination:

```python
page = store.search(("docs",), limit=20, offset=40)
```

## Optional Semantic Search

Semantic search is disabled by default. Enable it with an `index` config that provides dimensions and an embedding implementation.

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore(
    index={
        "dims": 1536,
        "embed": embeddings,
        "fields": ["text"],
    }
)

store.put(("docs",), "doc1", {"text": "Python tutorial", "kind": "guide"})
store.put(("docs",), "doc2", {"text": "TypeScript guide", "kind": "guide"})
results = store.search(("docs",), query="python programming", limit=5)
```

Index config notes:

- `embed` may be a LangChain `Embeddings` object or a compatible embedding function.
- `dims` must match the embedding vector length.
- `fields` selects which value fields to embed; omit it to use the whole value (`"$"`).
- Install `numpy` for better vector-search performance.
- No vectors are created unless an `index` config is supplied.

## Async Methods

`InMemoryStore` supports async operations as well:

```python
await store.aput(("users", "123"), "prefs", {"theme": "dark"})
item = await store.aget(("users", "123"), "prefs")
results = await store.asearch(("users",), filter={"theme": "dark"})
```

If the store has async embeddings, semantic search can await embedding calls.

## Compile-Time Use

Pass the store to graph compilation when graph nodes need access to long-term memory:

```python
store = InMemoryStore()
graph = builder.compile(checkpointer=checkpointer, store=store)
```

Pairing recommendations:

- Use `InMemorySaver` plus `InMemoryStore` for small tests.
- Use `SqliteSaver` plus `InMemoryStore` for local checkpoint persistence while prototyping store logic.
- Use `PostgresSaver` plus a durable store backend for production durability.

## Validation Checklist

- Write an item with `put`, read it with `get`, and assert `item.value`.
- Search by namespace prefix and a simple filter.
- If using semantic search, assert result ordering or non-empty scores for a tiny fixture.
- Confirm memory lifetime expectations: `InMemoryStore` data disappears on process restart.
- Confirm values are dictionaries; non-dict payloads do not match the store item model.

## Common Mistakes

- Confusing `thread_id` checkpoint memory with store namespaces. Checkpoints resume graph state; stores hold application memory.
- Using ephemeral `InMemoryStore` for production data.
- Passing `index` fields that do not exist in stored values, resulting in missing vectors or poor search.
- Using an embedding dimension that does not match the actual vectors.
- Expecting semantic ranking without configuring `index`.
