# Python SDK API Clients

This reference summarizes the stable client surface used by agents writing code against a LangGraph API server.

## Imports

Prefer public imports from `langgraph_sdk`:

```python
from langgraph_sdk import get_client, get_sync_client
```

For compatibility checks, `langgraph_sdk.client` also re-exports top-level client classes and resource clients:

- Async: `LangGraphClient`, `HttpClient`, `AssistantsClient`, `ThreadsClient`, `RunsClient`, `CronClient`, `StoreClient`.
- Sync: `SyncLangGraphClient`, `SyncHttpClient`, `SyncAssistantsClient`, `SyncThreadsClient`, `SyncRunsClient`, `SyncCronClient`, `SyncStoreClient`.
- JSON helpers and loopback utility: `_aencode_json`, `_adecode_json`, `_encode_json`, `_decode_json`, `configure_loopback_transports`.

Use the bundled inspection helper to verify those exports in the active environment:

```bash
python skills/langgraph/sub-skills/sdk-clients/scripts/inspect_sdk_exports.py
```

## Factory Signatures

`get_client` and `get_sync_client` share the same core parameters:

```python
get_client(*, url=None, api_key=sentinel, headers=None, timeout=None)
get_sync_client(*, url=None, api_key=sentinel, headers=None, timeout=None)
```

Meaning:

- `url`: API base URL. Use an explicit URL for ordinary scripts and apps.
- `api_key`: string for a bearer credential, `None` to disable environment lookup, or omitted to auto-load from environment.
- `headers`: mapping of extra request headers merged with auth headers.
- `timeout`: `httpx.Timeout`, float seconds, or `(connect, read, write, pool)` tuple.

Default timeout behavior is suitable for long graph runs: connect 5 seconds, read 300 seconds, write 300 seconds, pool 5 seconds.

## Auth And Headers

When `api_key` is omitted, the SDK looks for API keys in this order:

1. `LANGGRAPH_API_KEY`
2. `LANGSMITH_API_KEY`
3. `LANGCHAIN_API_KEY`

Use these patterns:

```python
# Local development server with no auth.
client = get_client(url="http://localhost:8123", api_key=None)

# Remote server; key comes from LANGGRAPH_API_KEY or fallback env vars.
client = get_client(url="https://example.langgraph.app")

# Explicit token from a secret manager; do not commit the literal value.
client = get_client(url=server_url, api_key=token)

# Request-scoped metadata header.
client = get_client(
    url=server_url,
    api_key=token,
    headers={"X-Trace-Source": "agent-workflow"},
)
```

Avoid printing client headers or environment variables in logs. If you need to demonstrate setup, use placeholders such as `export LANGGRAPH_API_KEY=...`.

## Async Client Usage

Async code must `await` resource methods:

```python
from langgraph_sdk import get_client

async with get_client(url="http://localhost:8123", api_key=None) as client:
    assistants = await client.assistants.search()
    thread = await client.threads.create()
    run = await client.runs.create(
        thread["thread_id"],
        assistants[0]["assistant_id"],
        input={"messages": [{"role": "user", "content": "hi"}]},
    )
```

`get_client(url=None)` has special server-internal behavior: it attempts an in-process ASGI transport for code running inside a LangGraph server. For normal client scripts, pass a real server URL.

## Sync Client Usage

Sync code must not use `await`:

```python
from langgraph_sdk import get_sync_client

with get_sync_client(url="http://localhost:8123", api_key=None) as client:
    assistants = client.assistants.search()
    thread = client.threads.create()
    run = client.runs.create(
        thread["thread_id"],
        assistants[0]["assistant_id"],
        input={"messages": [{"role": "user", "content": "hi"}]},
    )
```

`get_sync_client()` defaults to `http://localhost:8123` when `url` is omitted. Prefer explicit URLs in reusable code.

## Resource Client Map

Use these attributes on either async or sync top-level clients:

| Attribute | Purpose |
| --- | --- |
| `assistants` | Search, get, create, update, and manage assistant/graph configurations. |
| `threads` | Create threads, inspect state/history, copy/delete threads, and open thread streams. |
| `runs` | Start, wait for, stream, join, cancel, and inspect runs. |
| `crons` | Manage scheduled runs. |
| `store` | Work with the server persistent document store. |
| `http` | Underlying request helper for low-level needs. |

For graph behavior, state schemas, and invocation details, route to `graph-runtime`. For checkpointers and long-term store design, route to `persistence`.

## Safe Validation Without Network

Run:

```bash
python skills/langgraph/sub-skills/sdk-clients/scripts/inspect_sdk_exports.py --json
```

A healthy environment reports:

- `ok: true`
- callable public factories
- present async and sync client classes
- present resource client classes
- auth fallback order `LANGGRAPH_API_KEY`, `LANGSMITH_API_KEY`, `LANGCHAIN_API_KEY`

This check imports the installed package only; it does not contact a LangGraph server and does not read credentials.
