# Checkpointing Reference

This reference helps future agents choose and wire LangGraph checkpoint persistence without depending on the original repository checkout.

## What Checkpoints Persist

A checkpointer saves graph state at graph supersteps. This enables:

- Memory across invocations in the same thread.
- Human-in-the-loop pauses and resumes.
- Durable execution after failures.
- Time travel or explicit resume from a `checkpoint_id`.
- Pending writes preservation when one node fails after other nodes in the same step completed.

A checkpoint tuple contains the saved checkpoint, config, metadata, parent config, and pending writes. Most app code should interact through compiled graph methods such as `invoke`, `stream`, `get_state`, and `update_state` rather than manually constructing checkpoints.

## Thread Config

When a graph is compiled with a checkpointer, every run that should persist or resume state needs a config with `thread_id`:

```python
config = {"configurable": {"thread_id": "conversation-42"}}
result = graph.invoke(inputs, config)
```

Use `thread_id` as the durable conversation, user session, job, or workflow execution identifier. Reuse it to continue state; generate a new one for independent runs.

Optional fields:

```python
config = {
    "configurable": {
        "thread_id": "conversation-42",
        "checkpoint_ns": "",
        "checkpoint_id": "1ef4f797-8335-6428-8001-8a1503f9b875",
    }
}
```

- `checkpoint_id` resumes or reads from a specific checkpoint inside a thread.
- `checkpoint_ns` separates checkpoint namespaces inside a thread. Most app code can omit it or use `""`.

## Saver Selection

| Need | Saver | Package | Notes |
| --- | --- | --- | --- |
| Unit tests, demos, debugging | `InMemorySaver` | `langgraph-checkpoint` / LangGraph install | Process memory only; lost on exit. |
| Local sync persistence | `SqliteSaver` | `langgraph-checkpoint-sqlite` | Lightweight SQLite; sync graph calls only. |
| Local async persistence | `AsyncSqliteSaver` | `langgraph-checkpoint-sqlite` plus `aiosqlite` | Import from `langgraph.checkpoint.sqlite.aio`. |
| Production sync durability | `PostgresSaver` | `langgraph-checkpoint-postgres` | Call `setup()` before first use. |
| Production async durability | `AsyncPostgresSaver` | `langgraph-checkpoint-postgres` | Use async context and `await checkpointer.setup()`. |

## InMemorySaver

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)
result = graph.invoke(inputs, {"configurable": {"thread_id": "test-thread"}})
```

Constructor:

```python
InMemorySaver(*, serde=None, factory=defaultdict)
```

Use it to verify graph logic and persistence behavior quickly. It supports sync and async context manager usage, but it is not durable.

## SQLite Saver

```python
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("checkpoints.sqlite") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
    graph.invoke(inputs, {"configurable": {"thread_id": "local-thread"}})
```

Constructor and factory:

```python
SqliteSaver(conn, *, serde=None)
SqliteSaver.from_conn_string(":memory:")
SqliteSaver.from_conn_string("checkpoints.sqlite")
```

Operational notes:

- `from_conn_string` creates a SQLite connection with `check_same_thread=False` and closes it on context exit.
- `setup()` is called automatically by saver operations; user code generally does not need to call it directly.
- The sync saver raises informative `NotImplementedError` messages for async methods and points to `AsyncSqliteSaver`.
- Metadata filters support exact JSON-style filtering and reject unsafe filter keys.
- `list(config, filter=..., before=..., limit=...)` returns newest checkpoints first.

Async SQLite:

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async with AsyncSqliteSaver.from_conn_string("checkpoints.sqlite") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
    result = await graph.ainvoke(inputs, {"configurable": {"thread_id": "async-local"}})
```

Install `aiosqlite` if the async import or runtime path fails.

## Postgres Saver

```python
from langgraph.checkpoint.postgres import PostgresSaver

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()
    graph = builder.compile(checkpointer=checkpointer)
    graph.invoke(inputs, {"configurable": {"thread_id": "prod-thread"}})
```

Constructor and factory:

```python
PostgresSaver(conn, pipe=None, serde=None)
PostgresSaver.from_conn_string(DB_URI, pipeline=False)
```

Required first-use step:

```python
checkpointer.setup()
```

`setup()` creates checkpoint tables and runs migrations. Call it before first use of a database, during startup, migration, or provisioning. Repeated calls are safe when migrations are already applied.

Manual psycopg connection:

```python
from psycopg import Connection
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver

with Connection.connect(DB_URI, autocommit=True, prepare_threshold=0, row_factory=dict_row) as conn:
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()
```

Manual connection requirements:

- `autocommit=True` lets `setup()` persist migration/table creation.
- `row_factory=dict_row` is required because saver code accesses rows by column name, such as `row["checkpoint"]`.
- `prepare_threshold=0` is used by the factory and repo tests for predictable psycopg behavior.

Connection pools are supported through psycopg pool objects. If using `ConnectionPool`, set `kwargs={"autocommit": True, "row_factory": dict_row}`. Pipelines are only valid with a single connection, not a `ConnectionPool`.

## Metadata Queries

Savers expose:

```python
list(checkpointer.list(config, filter={"source": "input"}, limit=10))
list(checkpointer.list(None, filter={"step": 1}))
list(checkpointer.list(config, before=older_checkpoint_config))
```

Behavior to rely on:

- `filter` matches checkpoint metadata keys and values.
- `config={"configurable": {"thread_id": "..."}}` lists checkpoints for that thread, including namespaces.
- `before` limits results to checkpoints older than the given checkpoint config.
- `limit=0` returns no rows; `limit=None` returns all matches.

## Serde Security

The default checkpoint serializer supports many Python types. Persistent or shared checkpoint stores should restrict deserialization.

Environment hardening:

```bash
export LANGGRAPH_STRICT_MSGPACK=true
```

Explicit allowlist:

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

serde = JsonPlusSerializer(
    allowed_msgpack_modules=[("my_app.models", "UserState")]
)
checkpointer = InMemorySaver(serde=serde)
```

Strict behavior blocks unregistered types and falls back to safe serialized data. Allowlisting preserves specific trusted custom types without allowing arbitrary imports.

## Migration Pattern: Stateless to Persistent

1. Choose a backend: SQLite for local development, Postgres for production.
2. Instantiate the saver near graph construction, not inside each node.
3. Compile with `builder.compile(checkpointer=checkpointer)`.
4. Update every graph call to include `config={"configurable": {"thread_id": stable_id}}`.
5. Reuse `thread_id` for continuity; change it for a fresh conversation/job.
6. Add strict msgpack or an allowlist before connecting to persistent data.
7. Validate by invoking twice with the same `thread_id` and checking `graph.get_state(config)` or saver `list(config)`.

## Expected Smoke Output

The bundled [memory checkpoint smoke script](../scripts/smoke_memory_checkpoint.py) prints JSON similar to:

```json
{
  "ok": true,
  "first_result": {"count": 1},
  "second_result": {"count": 2},
  "checkpoint_count": 2,
  "thread_id": "skill-smoke-thread"
}
```

If `checkpoint_count` is `0` or the second empty-input call does not resume and increment the previous state, check that the graph is compiled with `checkpointer=...` and every call uses the same `thread_id`.
