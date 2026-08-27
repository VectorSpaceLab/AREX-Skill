---
name: sdk-clients
description: "Use LangGraph Python SDK clients, API resource clients, auth
  headers, and thread-centric streaming v3; understand JS SDK status."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# sdk-clients

Use this sub-skill when an agent needs to connect Python code to a running LangGraph API server, manage API resources, or convert polling/run streaming code to thread-centric streaming v3.

## Choose This Sub-Skill For

- Creating async or sync SDK clients with `get_client()` or `get_sync_client()`.
- Configuring local no-key clients, remote API-key clients, custom headers, or HTTP timeouts.
- Calling resource clients for assistants, threads, runs, cron jobs, and the persistent store.
- Using `client.threads.stream()` with typed projections such as `messages`, `tool_calls`, `values`, `output`, `subgraphs`, and `extensions`.
- Explaining reconnect limits, SSE vs WebSocket transport, sync vs async behavior, and JS SDK repository status.

For graph authoring and invocation semantics, use [graph-runtime](../graph-runtime/SKILL.md). For prebuilt agent helpers that produce assistant graphs, use [prebuilt-agents](../prebuilt-agents/SKILL.md). For checkpoint and store persistence details, use [persistence](../persistence/SKILL.md). For starting or deploying the API server, use [cli-deployment](../cli-deployment/SKILL.md) when present.

## Quick Install And Smoke Check

Install the Python SDK in the target project environment:

```bash
python -m pip install langgraph-sdk
```

Check that the expected exports are present without contacting a server:

```bash
python skills/langgraph/sub-skills/sdk-clients/scripts/inspect_sdk_exports.py --json
```

Expected result: JSON with `ok: true`, callable `get_client` and `get_sync_client`, async/sync top-level client classes, resource client exports, and the auth environment fallback order.

## Client Factories

The public factories are:

```python
from langgraph_sdk import get_client, get_sync_client

async_client = get_client(
    url="http://localhost:8123",
    api_key=None,
    headers={"X-Request-Source": "agent"},
    timeout=30.0,
)

sync_client = get_sync_client(url="http://localhost:8123", api_key=None)
```

Parameter notes:

- `url` is the LangGraph API base URL. `get_sync_client()` defaults to `http://localhost:8123` when omitted.
- `get_client(url=None)` is async and first attempts an in-process server transport when used inside a LangGraph server; otherwise give an explicit URL for normal scripts.
- `api_key` accepts a string, `None`, or the default sentinel. A string becomes the bearer credential; `None` disables environment key lookup.
- When `api_key` is omitted, keys auto-load in order: `LANGGRAPH_API_KEY`, then `LANGSMITH_API_KEY`, then `LANGCHAIN_API_KEY`.
- `headers` merges additional HTTP headers with auth headers. Do not hard-code secrets in source; prefer environment variables.
- `timeout` accepts an `httpx.Timeout`, a float total timeout, or a `(connect, read, write, pool)` tuple. Defaults are connect 5s, read 300s, write 300s, pool 5s.

Use context managers in long-running apps so the underlying HTTP client closes cleanly:

```python
async with get_client(url=server_url, api_key=token) as client:
    assistants = await client.assistants.search()

with get_sync_client(url=server_url, api_key=token) as client:
    assistants = client.assistants.search()
```

More client details: [references/api-clients.md](references/api-clients.md).

## API Resource Clients

Top-level clients expose these resources:

- `client.assistants` for graph assistant configuration and lookup.
- `client.threads` for conversational threads, state, history, and thread-centric streaming.
- `client.runs` for starting, waiting, joining, cancelling, and streaming runs.
- `client.crons` for scheduled runs.
- `client.store` for persistent document store operations.
- `client.http` for lower-level request helpers when a resource method is not enough.

Keep async and sync styles separate. Await async resource calls from `get_client()`. Do not await sync calls from `get_sync_client()`.

## Thread-Centric Streaming v3

Prefer `client.threads.stream()` when a workflow needs one thread session with multiple typed views over the same run. The call returns a context manager. `assistant_id` is required. If `thread_id` is omitted, the SDK mints a UUIDv4 client-side and the server creates the thread lazily on first `run.start`.

```python
import asyncio
from langgraph_sdk import get_client

client = get_client(url="http://localhost:8123", api_key=None)

async with client.threads.stream(assistant_id="agent") as thread:
    await thread.run.start(input={"messages": [{"role": "user", "content": "hi"}]})

    async def collect_messages():
        return [stream async for stream in thread.messages]

    async def collect_tools():
        return [call async for call in thread.tool_calls]

    messages, tool_calls = await asyncio.gather(collect_messages(), collect_tools())
    final_values = await thread.output
```

Important streaming rules:

- Start projections concurrently when you need multiple views from the same run; typed projections share the underlying event stream.
- Use `async with` for async streams and `with` for sync streams. Calling `run.start()` or subscribing outside the context manager raises a runtime error.
- `headers` passed to `threads.stream()` are forwarded to command and event requests for that stream session.
- `transport="sse"` is the default. Async thread streaming can use `transport="websocket"` when the `websockets` optional dependency is installed and the server supports it.
- Reconnect attempts are limited to 5 by default for shared stream and lifecycle handling. Persistent network partitions surface as runtime failures on active projections.
- Each `thread.extensions[name]` access creates a subscription. Assign it once and reuse it inside the session to avoid duplicate extension subscriptions.

More streaming patterns and conversion guidance: [references/thread-streaming.md](references/thread-streaming.md).

## JS SDK Status

The JavaScript/TypeScript SDK content has moved out of this repository to the public LangGraph.js repository. For JS/TS clients, use [LangGraph.js](https://github.com/langchain-ai/langgraphjs/tree/main/libs/sdk) and the [LangGraph.js docs](https://docs.langchain.com/oss/javascript/langgraph/overview). Do not infer current JS SDK APIs from this repository beyond that migration notice.

## Validation Checklist

- `python -m pip show langgraph-sdk` succeeds in the environment that will run the client code.
- `python skills/langgraph/sub-skills/sdk-clients/scripts/inspect_sdk_exports.py` reports `OK: langgraph-sdk client exports available`.
- Local API tests use `api_key=None` unless the local server actually requires auth.
- Remote API tests pass credentials through `LANGGRAPH_API_KEY` or a secret manager, not literals committed to source.
- Async code awaits `client.assistants`, `client.threads`, `client.runs`, `client.crons`, and `client.store` methods; sync code does not.
- Streaming code enters the context manager before `run.start()` and consumes required projections before exiting.

## Troubleshooting Router

- Import, install, optional dependency, auth, timeout, and local/remote server issues: [references/troubleshooting.md](references/troubleshooting.md).
- Client factory parameters, auth fallback, and resource inventory: [references/api-clients.md](references/api-clients.md).
- Streaming conversion, projections, transport choices, and reconnect limitations: [references/thread-streaming.md](references/thread-streaming.md).
- Use [scripts/inspect_sdk_exports.py](scripts/inspect_sdk_exports.py) to verify installed exports without credentials or network.
