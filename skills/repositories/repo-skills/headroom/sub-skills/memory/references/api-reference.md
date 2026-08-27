# Headroom memory API reference

This reference covers memory-specific Python APIs. Use the root or `sdk` sub-skill for non-memory compression APIs.

## Public imports

```python
from headroom.memory import (
    Memory,
    MemoryResult,
    with_memory,
    with_memory_tools,
    LocalBackend,
    LocalBackendConfig,
    HierarchicalMemory,
    MemoryConfig,
    EmbedderBackend,
    VectorBackend,
    TextBackend,
)
```

The package root also lazily exposes `Memory`, `with_memory`, `HierarchicalMemory`, `MemoryConfig`, and `EmbedderBackend`. If memory extras are not installed, optional root exports can resolve to `None`; prefer importing from `headroom.memory` when diagnosing memory installs.

## Zero-config `Memory` class

`Memory` is the simplest async API. It defaults to a local embedded backend and has no external service requirement.

Verified signature shape:

```text
Memory(
  backend="local",
  db_path=None,
  qdrant_url=None,
  qdrant_host=None,
  qdrant_port=None,
  qdrant_api_key=None,
  neo4j_uri="neo4j://localhost:7687",
  neo4j_user="neo4j",
  neo4j_password="password",
)
```

Primary async methods:

```python
memory = Memory(db_path="./app-memory.db")
try:
    memory_id = await memory.save(
        "User prefers Python for CLI tooling",
        user_id="alice",
        importance=0.8,
        facts=["User prefers Python for CLI tooling"],
        entities=[{"entity": "Python", "entity_type": "technology"}],
        metadata={"source": "onboarding"},
    )

    results = await memory.search(
        "preferred programming language",
        user_id="alice",
        top_k=5,
        include_graph=True,
    )
    for result in results:
        print(result.id, result.score, result.content)

    deleted = await memory.delete(memory_id)
finally:
    await memory.close()
```

`MemoryResult` contains `content`, `score`, `id`, and `metadata`.

### Local backend behavior

- `backend="local"` uses embedded SQLite storage, a vector index, FTS5 text search, a cache layer, and a local graph store. It is the safe default for development, tests, and private app memory.
- If `db_path` is omitted, Headroom uses its workspace memory database. For experiments, pass an explicit temp or app-owned `db_path` so you do not pollute a user's normal memory store.
- `user_id` is required for save/search and is the broadest isolation scope.
- `session_id`, `agent_id`, and `turn_id` are available in lower-level APIs and wrappers for narrower scope.

### Service-backed memory

`Memory(backend="qdrant-neo4j")` switches to an external Qdrant + Neo4j backed adapter. Use it only when the services are running and dependencies are installed.

Configuration options:

- `qdrant_url` or `HEADROOM_QDRANT_URL` for hosted/custom Qdrant.
- `qdrant_host` / `qdrant_port` or corresponding `HEADROOM_QDRANT_*` environment variables for local Qdrant.
- `qdrant_api_key` or `HEADROOM_QDRANT_API_KEY` for hosted Qdrant.
- `neo4j_uri`, `neo4j_user`, and `neo4j_password` for Neo4j.

Do not paste secrets into code examples or skill files. Prefer environment variables or a secret manager.

## `with_memory`: sync chat wrapper with inline extraction

`with_memory(client, user_id, db_path="headroom_memory.db", top_k=5, session_id=None, agent_id=None, embedder_backend=EmbedderBackend.LOCAL, openai_api_key=None, **kwargs)` wraps an OpenAI-compatible synchronous client.

Runtime flow:

1. Search relevant memories before each call.
2. Prepend a `<context>` block to the first user message, preserving the original system prompt for provider cache behavior.
3. Add an inline memory extraction instruction to the system prompt.
4. Call the original client's `chat.completions.create`.
5. Parse memory blocks from the response and store extracted memories.
6. Return a cleaned response with the memory block removed.

Example:

```python
from openai import OpenAI
from headroom.memory import with_memory

client = with_memory(
    OpenAI(),
    user_id="alice",
    db_path="./app-memory.db",
    top_k=3,
    session_id="support-chat-42",
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "I prefer concise Python examples."}],
)

# Direct sync memory operations are exposed on the wrapper.
client.memory.add("User prefers concise Python examples", importance=0.8)
print([m.content for m in client.memory.search("verbosity preference")])
```

Use `with_memory` for synchronous OpenAI-compatible clients. In an already-running async event loop, prefer the explicit async `Memory` API or `with_memory_tools(...).chat.completions.acreate(...)`.

## `with_memory_tools`: explicit function-calling memory tools

`with_memory_tools` adds memory tool definitions to each chat request and can auto-handle tool calls.

```python
from openai import OpenAI
from headroom.memory import LocalBackend, LocalBackendConfig, with_memory_tools

backend = LocalBackend(LocalBackendConfig(db_path="./app-memory.db", embedder_backend="onnx"))
client = with_memory_tools(
    OpenAI(),
    backend=backend,
    user_id="alice",
    session_id="sess-1",
    optimized=True,
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Remember that this project uses Postgres."}],
)
if hasattr(response, "_memory_tool_results"):
    print(response._memory_tool_results)
```

Tool names are `memory_save`, `memory_search`, `memory_update`, `memory_delete`, and `memory_list` in the tool schema. `MemorySystem.process_tool_call` handles save/search/update/delete; list is defined for model-facing browsing but is not dispatched by `MemorySystem` in this version.

Optimized mode changes `memory_save` by allowing `facts`, `extracted_entities`, `extracted_relationships`, and `background`. A backend that supports these fields can avoid redundant extraction calls. If a backend rejects those fields, the wrapper falls back to the basic save call.

Sync and async completions are available:

- `client.chat.completions.create(...)` for sync clients.
- `await client.chat.completions.acreate(...)` for async use; it uses async client methods when present and otherwise runs sync calls in an executor.

## `MemoryConfig`, `HierarchicalMemory`, and backends

Use these when you need explicit component control:

```python
from pathlib import Path
from headroom.memory import HierarchicalMemory, MemoryConfig, EmbedderBackend, VectorBackend

config = MemoryConfig(
    db_path=Path("./memory.db"),
    embedder_backend=EmbedderBackend.ONNX,
    vector_backend=VectorBackend.AUTO,
    vector_dimension=384,
    cache_enabled=True,
    auto_bubble=True,
    bubble_threshold=0.7,
)

memory = await HierarchicalMemory.create(config)
created = await memory.add(
    content="User prefers pytest for tests",
    user_id="alice",
    session_id="sess-1",
    importance=0.9,
)
results = await memory.search("test framework preference", user_id="alice", top_k=5)
updated = await memory.supersede(created.id, "User now prefers pytest with hypothesis")
history = await memory.get_history(updated.id, include_future=True)
await memory.close()
```

Important configuration facts:

- `MemoryConfig` defaults include SQLite storage, vector backend `AUTO`, text backend `FTS5`, vector dimension `384`, cache enabled, auto-bubbling enabled, and bubble threshold `0.7`.
- Embedder choices are `LOCAL`, `ONNX`, `OPENAI`, and `OLLAMA`. `OPENAI` requires an API key. `OLLAMA` uses an Ollama base URL. `ONNX` is the preferred lightweight local runtime when available.
- `VectorBackend.AUTO` prefers `sqlite-vec`, then HNSW. Missing vector dependencies fail with install guidance.
- `StoreBackend.EXTERNAL`, `VectorBackend.EXTERNAL`, and `TextBackend.EXTERNAL` load setuptools entry points named by the corresponding config field.

## `LocalBackend` direct API

`LocalBackend` is useful for tools, MCP, and direct storage operations:

```python
from headroom.memory import LocalBackend, LocalBackendConfig

backend = LocalBackend(LocalBackendConfig(
    db_path="./memory.db",
    embedder_backend="onnx",
    graph_persist=True,
))
try:
    mem = await backend.save_memory(
        content="Alice owns the API migration",
        user_id="alice",
        importance=0.8,
        extracted_entities=[{"entity": "Alice", "entity_type": "person"}],
        extracted_relationships=[],
    )
    hits = await backend.search_memories("who owns migration", user_id="alice", include_related=True)
    text_hits = await backend.text_search("API", user_id="alice")
finally:
    await backend.close()
```

Direct methods include `save_memory`, `search_memories`, `text_search`, `hybrid_search`, `update_memory`, `detach_supersession`, `delete_memory`, `get_memory`, `get_user_memories`, `clear_user`, `get_graph`, and `query_subgraph`.

## Markdown bridge and cross-agent sync APIs

Memory bridge and sync APIs are for interoperability with agent-native memory files.

- `MemoryBridge(BridgeConfig(...), backend)` can import markdown memory files into Headroom, export Headroom memories back to markdown, and run bidirectional sync with hash-based change detection.
- `headroom.memory.sync.sync(backend, adapter, user_id, force=False)` synchronizes a Headroom DB with an agent adapter. Built-in sync adapters cover Claude Code and Codex; the sync subprocess CLI accepts `--db`, `--user`, `--agent claude|codex`, and `--force`.

Treat bridge/sync writes as user-state mutations. Preview target files and make backups when changing real agent memory files.
