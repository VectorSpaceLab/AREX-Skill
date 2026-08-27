# Persistence Troubleshooting

Use this guide when checkpointing, stores, SQLite, Postgres, thread config, async usage, or serde security fails.

## Install And Import Failures

### `ModuleNotFoundError: langgraph.checkpoint.sqlite`

Install the SQLite checkpoint package:

```bash
pip install langgraph-checkpoint-sqlite
```

For project managers that use `uv`:

```bash
uv add langgraph-checkpoint-sqlite
```

### `ModuleNotFoundError: aiosqlite`

`AsyncSqliteSaver` requires `aiosqlite`:

```bash
pip install aiosqlite
```

Then import the async saver explicitly:

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
```

### `ModuleNotFoundError: psycopg` Or `psycopg_pool`

Install the Postgres checkpoint package:

```bash
pip install langgraph-checkpoint-postgres
```

If local psycopg compilation or system libraries are the problem, use a supported psycopg install option such as `psycopg[binary]` according to Psycopg 3 installation guidance.

## Missing `thread_id`

Symptom examples:

- Graph state does not resume.
- Checkpoint list is empty for expected runs.
- LangGraph complains about missing configurable keys.

Fix every persistent graph call:

```python
config = {"configurable": {"thread_id": "stable-session-id"}}
graph.invoke(inputs, config)
```

Use the same `thread_id` to continue a conversation or workflow. Use a new `thread_id` for a fresh independent run.

## Sync vs Async Confusion

### SQLite sync saver used with async graph methods

`SqliteSaver` does not implement async methods. If the app uses `ainvoke`, `astream`, or async graph execution, switch to:

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async with AsyncSqliteSaver.from_conn_string("checkpoints.sqlite") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
    await graph.ainvoke(inputs, {"configurable": {"thread_id": "async-thread"}})
```

### Postgres sync saver used in async app

Use `AsyncPostgresSaver` from `langgraph.checkpoint.postgres.aio` and await setup when using async execution.

## Postgres Setup Failures

### Missing checkpoint tables or migrations

Call `setup()` before first use of a Postgres checkpoint database:

```python
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()
```

For async Postgres, use the async saver and await setup.

### `TypeError: tuple indices must be integers or slices, not str`

Cause: a manual psycopg connection is using the default tuple row factory. `PostgresSaver` reads rows with dictionary-style access such as `row["checkpoint"]`.

Fix:

```python
from psycopg import Connection
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver

with Connection.connect(DB_URI, autocommit=True, prepare_threshold=0, row_factory=dict_row) as conn:
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()
```

Also set `row_factory=dict_row` in `ConnectionPool` kwargs:

```python
ConnectionPool(DB_URI, kwargs={"autocommit": True, "row_factory": dict_row})
```

### Tables created but disappear or are not visible

Cause: manual connection omitted `autocommit=True`, so setup migrations may not have been committed.

Fix manual connections with:

```python
Connection.connect(DB_URI, autocommit=True, row_factory=dict_row)
```

## SQLite Issues

### SQLite file does not persist

Use a filesystem database path rather than `":memory:"`:

```python
SqliteSaver.from_conn_string("checkpoints.sqlite")
```

Remember that a context manager closes the connection on exit. Keep the saver alive for the graph operations that need it.

### Async errors mention `AsyncSqliteSaver`

That is expected when async methods are called on sync `SqliteSaver`. Install `aiosqlite` and switch imports.

### Metadata filter raises `ValueError: Invalid filter key`

Checkpoint metadata filters reject unsafe or malformed keys to prevent SQL injection. Use normal key paths such as:

```python
{"source": "input"}
{"user.access-level": "public"}
{"123abc": "ok"}
```

Do not pass raw SQL fragments as filter keys.

## Serde And Security Warnings

### Warning about unregistered msgpack type

The serializer encountered a custom Python type that is not allowlisted. For development, decide whether the type should be persisted as a typed object or as safe structured data.

Strict mode:

```bash
export LANGGRAPH_STRICT_MSGPACK=true
```

Allowlist trusted custom types:

```python
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

serde = JsonPlusSerializer(
    allowed_msgpack_modules=[("my_app.state", "UserState")]
)
checkpointer = InMemorySaver(serde=serde)
```

Use strict mode or explicit allowlists before reading checkpoint data from a persistent database that could be modified outside the app.

### Blocked custom type becomes a dictionary

In strict mode, unregistered custom objects may be restored as safe serialized data rather than the original Python object. Add a narrow allowlist only if the class is trusted and required by application logic.

## Store Issues

### `InMemoryStore` data disappears

This is expected. `InMemoryStore` is process-local. Use it for tests and prototypes, or replace it with a durable store backend for production.

### Semantic search returns unranked or empty results

Check that:

- `InMemoryStore(index={...})` was configured.
- `dims` matches embedding vector length.
- `embed` is a valid embedding object or function.
- `fields` names exist in the stored value dictionaries.
- Items were inserted after the store was created with the index config.

### Store filters do not match

Store filters operate on item `value` dictionaries. Confirm the value is a dict and the target keys are top-level fields unless using a store/backend that documents nested filtering.

## Quick Isolation Steps

1. Run [the bundled memory checkpoint smoke script](../scripts/smoke_memory_checkpoint.py).
2. If the smoke script fails to import, fix package installation before app code.
3. If the smoke script passes, reproduce with the target saver and a tiny graph before debugging full agent logic.
4. Print or log the exact runtime config; verify `configurable.thread_id` is stable.
5. For Postgres, verify `setup()`, `autocommit=True`, `row_factory=dict_row`, database reachability, and credentials.
6. For async apps, verify every saver and graph call is async-compatible.

## Source Script Exclusions

No original repository examples, tests, notebooks, or scripts are required at runtime for this sub-skill. The bundled smoke script is a self-contained adaptation that uses public LangGraph package APIs only and requires no credentials, network, or destructive writes.
