# Thread-Centric Streaming v3

Thread-centric streaming v3 lets one client session own a thread, send commands, and consume typed projections over a shared event stream.

## When To Use It

Use `client.threads.stream()` when code needs:

- A single session for one `thread_id` and `assistant_id`.
- Concurrent views of the same run, such as messages plus tool calls plus final values.
- Lower duplicate-stream risk than manually starting separate polling or run-stream loops.
- Projection-oriented code that reads `thread.messages`, `thread.tool_calls`, `thread.values`, `thread.output`, `thread.subgraphs`, or `thread.extensions`.

Use `client.runs.stream()` or `client.runs.wait()` for simpler run-level workflows that do not need multiple thread projections. For deployment/server startup, route to `cli-deployment` when present.

## Opening A Stream

Async:

```python
import asyncio
from langgraph_sdk import get_client

client = get_client(url="http://localhost:8123", api_key=None)

async with client.threads.stream(
    assistant_id="agent",
    headers={"X-Trace-Source": "projection-demo"},
) as thread:
    await thread.run.start(input={"messages": [{"role": "user", "content": "hi"}]})

    async def read_messages():
        return [message async for message in thread.messages]

    async def read_tool_calls():
        return [tool_call async for tool_call in thread.tool_calls]

    messages, tool_calls = await asyncio.gather(read_messages(), read_tool_calls())
    final_values = await thread.output
```

Sync:

```python
from langgraph_sdk import get_sync_client

client = get_sync_client(url="http://localhost:8123", api_key=None)

with client.threads.stream(assistant_id="agent") as thread:
    thread.run.start(input={"messages": [{"role": "user", "content": "hi"}]})
    messages = list(thread.messages)
    final_values = thread.output
```

Rules confirmed by SDK tests and implementation:

- `assistant_id` is required.
- `thread_id=None` mints a UUIDv4 client-side.
- `headers` are forwarded to both command requests and event-stream requests.
- Access after stream close either raises a runtime error or yields nothing for closed projections, depending on the projection path.
- `close()` is idempotent.

## Commands And Lifecycle

Within the context manager, use `thread.run.start(...)` to start a run. It sends a `run.start` command with the stream's `assistant_id`, the input, optional `config`, and optional `metadata`.

```python
await thread.run.start(
    input={"messages": [{"role": "user", "content": "summarize"}]},
    config={"recursion_limit": 5},
    metadata={"trace": "case-123"},
)
```

Command IDs are monotonic within a stream session. Sync command IDs are protected for concurrent callers.

Subscriptions wait until `run.start` is accepted. If `run_start_timeout` is set on `threads.stream(...)`, subscriptions waiting for an in-flight start can time out instead of waiting forever.

## Typed Projections

Common projections:

- `thread.events`: raw event stream projection.
- `thread.values`: state values snapshots.
- `thread.messages`: chat model message streams.
- `thread.tool_calls`: tool call handles.
- `thread.output`: final terminal state values as an awaitable in async code, or blocking value in sync code.
- `thread.subgraphs` / `thread.subagents`: child namespace projections.
- `thread.extensions[name]`: extension-specific payload stream.
- `thread.agent.get_tree(xray=True)`: fetch the assistant graph tree using stream headers.

Consume multiple async projections concurrently when they represent the same run. This avoids waiting for one projection to finish before another starts and helps the SDK share the stream cleanly.

## Extension Subscription Pitfall

Each `thread.extensions[name]` access opens a subscription. Do not repeatedly index the same name inside loops:

```python
# Good: one projection object reused for the session.
progress = thread.extensions["progress"]
async for event in progress:
    handle(event)
```

Avoid this pattern because it can create duplicate subscriptions:

```python
# Avoid: each access can subscribe again.
async for event in thread.extensions["progress"]:
    handle(event)
```

If multiple consumers need the same extension, assign it once and fan out in application code.

## Transport Choices

`threads.stream(..., transport="sse")` is the default and works for async and sync clients.

`threads.stream(..., transport="websocket")` selects WebSocket transport. The async WebSocket path requires the optional `websockets` package and server support. If unavailable, install the optional dependency or fall back to SSE.

Use SSE for the first implementation unless you have a concrete reason to require WebSockets.

## Reconnect Limits

The SDK attempts limited reconnection for stream interruptions:

- Shared stream reconnect attempts default to 5.
- Lifecycle watcher reconnect attempts default to 5.
- Async shared-stream backoff starts at 0.1 seconds and caps at 2 seconds.
- Sync shared-stream controller defaults also use 5 attempts; sync controller backoff is exponential and jittered.
- Persistent partitions or exhausted reconnects surface as runtime errors on active projections.

Do not promise infinite resume. Application code that must survive longer outages should catch stream errors, log sanitized context, and create a new stream session from a known checkpoint or thread state.

## Converting Polling To Projections

When converting code that polls `runs.get()` or waits for `runs.wait()`:

1. Keep the existing `assistant_id`, `input`, `config`, and `metadata` shape.
2. Open `client.threads.stream(thread_id=existing_or_none, assistant_id=assistant_id)`.
3. Call `thread.run.start(...)` once inside the context manager.
4. Replace polling loops with typed projection consumers.
5. Gather concurrent projections before awaiting final output.
6. Reuse extension projection objects to avoid duplicate subscriptions.
7. Close the context manager promptly after the needed projections and final output are consumed.

Validation ideas:

- Confirm the final values match the old polling workflow for a tiny input.
- Confirm headers required by auth or tracing are passed through `threads.stream(headers=...)`.
- Simulate an extension projection and check that the code accesses `thread.extensions["name"]` once per session.

## Native Verification Candidates

The upstream SDK tests exercise these behaviors and are useful native candidates for later verification in a repository checkout:

- Client export compatibility.
- Async thread stream context manager, headers, transport selection, UUID minting, commands, projections, and reconnect behavior.
- Sync thread stream gates, reconnect backoff, command ID concurrency, close ordering, and projection behavior.

Runtime skill content should not depend on those original tests; use them only as external verification candidates during review.
