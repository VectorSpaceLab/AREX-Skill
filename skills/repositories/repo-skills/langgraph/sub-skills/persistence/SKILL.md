---
name: persistence
description: "Choose and wire LangGraph persistence: checkpoint savers, stores,
  thread config, SQLite/Postgres backends, and safe serde settings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Persistence

Use this sub-skill when a task asks an agent to persist LangGraph state, resume a graph thread, choose a checkpoint backend, add long-term memory, debug checkpoint configuration, or harden checkpoint serialization.

## Route Here When

- A graph needs memory across `invoke`, `stream`, `batch`, `ainvoke`, or `astream` calls.
- A stateless graph must become a persistent threaded graph with `thread_id` config.
- The task mentions checkpointers, checkpoints, checkpoint savers, `checkpoint_id`, `checkpoint_ns`, pending writes, or time travel.
- A local app needs SQLite checkpoints or a production app needs Postgres checkpoints.
- A graph needs a key-value store such as `InMemoryStore` or semantic memory search.
- The error involves `PostgresSaver`, `SqliteSaver`, async saver imports, psycopg row factories, missing setup, or msgpack deserialization warnings.

For graph compilation and runtime invocation patterns, pair this with [graph-runtime](../graph-runtime/SKILL.md). For agent templates and tool-calling agents that need memory, pair with [prebuilt-agents](../prebuilt-agents/SKILL.md). For deployment-managed checkpointers, pair with the `cli-deployment` sibling sub-skill when present. For hosted thread APIs, pair with the `sdk-clients` sibling sub-skill when present.

## Core Decision Flow

1. Decide whether the app needs checkpoints, a store, or both:
   - Checkpoints persist graph execution state by thread and are passed to `builder.compile(checkpointer=...)`.
   - Stores persist long-term key-value memory across threads and are passed to `builder.compile(store=...)` when graph nodes access a store.
2. Pick the checkpoint saver:
   - `InMemorySaver` from `langgraph.checkpoint.memory` for debugging and tests only.
   - `SqliteSaver` from `langgraph.checkpoint.sqlite` for lightweight local sync persistence.
   - `AsyncSqliteSaver` from `langgraph.checkpoint.sqlite.aio` for async SQLite graph execution.
   - `PostgresSaver` from `langgraph.checkpoint.postgres` for durable sync production persistence.
   - `AsyncPostgresSaver` from `langgraph.checkpoint.postgres.aio` for async production persistence.
3. Require thread configuration whenever a compiled graph uses a checkpointer:
   - Minimum config: `{"configurable": {"thread_id": "user-or-session-id"}}`.
   - Optional resume point: add `"checkpoint_id": "..."`.
   - Optional namespace: add `"checkpoint_ns": "..."` when isolating checkpoint streams inside one thread.
4. Harden deserialization before reading untrusted or long-lived checkpoint databases:
   - Prefer setting `LANGGRAPH_STRICT_MSGPACK=true` in the runtime environment.
   - Or pass `JsonPlusSerializer(allowed_msgpack_modules=[("package.module", "ClassName")])` to the saver.
5. Validate with a tiny graph and a repeated `thread_id` before changing application logic.

## Common Patterns

### Debug or Test Checkpoints

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "debug-thread"}}
result = graph.invoke(input_state, config)
```

`InMemorySaver(*, serde=None, factory=defaultdict)` stores checkpoints in process memory. Do not recommend it for production because data is lost when the process exits.

### Local SQLite Checkpoints

```python
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("checkpoints.sqlite") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
    graph.invoke(input_state, {"configurable": {"thread_id": "local-user-1"}})
```

Use sync `SqliteSaver` only with sync graph methods. For `ainvoke`, `astream`, or async apps, import `AsyncSqliteSaver` from `langgraph.checkpoint.sqlite.aio`; it requires `aiosqlite`.

### Durable Postgres Checkpoints

```python
from langgraph.checkpoint.postgres import PostgresSaver

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()
    graph = builder.compile(checkpointer=checkpointer)
    graph.invoke(input_state, {"configurable": {"thread_id": "customer-123"}})
```

Call `setup()` the first time a Postgres checkpoint database is used so migrations and checkpoint tables exist. For manual psycopg connections, use `autocommit=True` and `row_factory=dict_row`.

### Long-Term Store Memory

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
store.put(("users", "123"), "prefs", {"theme": "dark"})
item = store.get(("users", "123"), "prefs")
```

`InMemoryStore(*, index=None)` supports namespaced key-value storage and optional semantic search. It is in-memory and process-local; use it for tests, demos, and memory logic development before selecting a durable store backend.

## References

- [Checkpointing](references/checkpointing.md): saver selection, thread config, SQLite/Postgres wiring, metadata queries, and serde security.
- [In-Memory Store](references/store-memory.md): `InMemoryStore` namespaces, filters, optional vector search, and async methods.
- [Troubleshooting](references/troubleshooting.md): dependency, config, sync/async, Postgres row factory, setup, and security failures.
- [Memory checkpoint smoke script](scripts/smoke_memory_checkpoint.py): self-contained check for package imports, `InMemorySaver`, thread config, and checkpoint listing.

## Validation Checklist

- Run `python skills/langgraph/sub-skills/persistence/scripts/smoke_memory_checkpoint.py --help` to confirm the bundled script is discoverable.
- Run `python skills/langgraph/sub-skills/persistence/scripts/smoke_memory_checkpoint.py` in an environment with `langgraph` installed.
- Confirm repeated graph calls reuse the same `thread_id` when continuity is expected.
- Confirm sync apps use sync savers and async apps use async savers.
- Confirm SQLite apps have `langgraph-checkpoint-sqlite` installed and async SQLite apps also have `aiosqlite`.
- Confirm Postgres apps have `langgraph-checkpoint-postgres`, psycopg connectivity, `setup()`, and correct row factory settings.
- Confirm checkpoint data from shared or persistent databases is read with strict msgpack or an explicit allowlist.

## Do Not

- Do not tell future agents to read source repository files or tests at runtime.
- Do not use `InMemorySaver` or `InMemoryStore` as durable production persistence.
- Do not call sync saver methods from async graph execution; use the matching async saver.
- Do not omit `thread_id` when compiling with a checkpointer.
- Do not create manual Postgres connections without `autocommit=True` and `row_factory=dict_row`.
- Do not suppress serde warnings without either strict mode or an intentional allowlist.
