# SDK Client Troubleshooting

Use this guide when client code fails before or during calls to a LangGraph API server.

## Install And Import Failures

Symptom: `ModuleNotFoundError: No module named 'langgraph_sdk'`.

Fix:

```bash
python -m pip install langgraph-sdk
python skills/langgraph/sub-skills/sdk-clients/scripts/inspect_sdk_exports.py
```

If the script reports a missing export, check that the active interpreter is the one used by your app:

```bash
python -c "import sys; print(sys.executable)"
python -m pip show langgraph-sdk
```

Do not mix a system `pip` with a virtual environment `python`.

## Optional WebSocket Dependency

Symptom: WebSocket streaming import/runtime errors mentioning `websockets`.

Fix options:

- Prefer the default SSE transport: `client.threads.stream(..., transport="sse")`.
- If WebSocket transport is required, install a compatible `websockets` package in the application environment and confirm the server supports WebSocket thread streaming.

The async thread stream supports WebSocket transport. SSE is the default and safest baseline. Sync streaming uses SSE by default; avoid requiring WebSockets unless the installed SDK/server combination has been proven in your environment.

## Local No-Key Versus Remote Key Auth

For local no-auth development servers, explicitly disable environment key lookup:

```python
client = get_client(url="http://localhost:8123", api_key=None)
```

For remote servers, prefer environment variables:

```bash
export LANGGRAPH_API_KEY=...
```

```python
client = get_client(url=server_url)
```

If no explicit `api_key` is passed, lookup order is `LANGGRAPH_API_KEY`, `LANGSMITH_API_KEY`, then `LANGCHAIN_API_KEY`.

Security warnings:

- Do not commit API keys in examples, tests, notebooks, or logs.
- Do not print request headers when they may include authorization.
- Use placeholders in docs and bug reports.
- Use `api_key=None` only for trusted local servers or server configurations that intentionally do not require auth.

## Bad URL Or Server Not Running

Symptoms include connection refused, DNS errors, 404s on expected SDK endpoints, or timeouts before any run begins.

Checks:

```python
from langgraph_sdk import get_sync_client

with get_sync_client(url="http://localhost:8123", api_key=None, timeout=10.0) as client:
    print(client.assistants.search())
```

Fixes:

- Start the LangGraph API server before running SDK client code.
- Verify the base URL points to the API root, not a docs page or app frontend.
- For remote deployments, verify network access and required auth headers.
- For local sync code, remember `get_sync_client()` defaults to `http://localhost:8123`; explicit URLs are clearer.

## Sync Versus Async Confusion

Symptom: `TypeError`, un-awaited coroutine warnings, or code hangs in the wrong event loop.

Use one style consistently:

```python
# Async
async with get_client(url=server_url) as client:
    assistants = await client.assistants.search()

# Sync
with get_sync_client(url=server_url) as client:
    assistants = client.assistants.search()
```

Do not call sync clients from an async event loop for long-running requests if it blocks the loop. Do not use `await` with sync resource methods.

## Stream Used Outside Context Manager

Symptoms:

- `AsyncThreadStream not entered — use async with`.
- `SyncThreadStream not entered — use with`.
- `closed` runtime errors after leaving the context manager.

Fix:

```python
async with client.threads.stream(assistant_id="agent") as thread:
    await thread.run.start(input={"messages": []})
    final = await thread.output
```

The stream owns transports, lifecycle watchers, subscriptions, and active message/tool handles. Keep all `run.start`, projection consumption, and final output reads inside the context manager.

## Duplicate Extension Subscriptions

Symptom: duplicate progress/custom events or unexpected extra stream subscriptions.

Cause: each `thread.extensions[name]` access can open a new subscription.

Fix:

```python
progress = thread.extensions["progress"]
async for event in progress:
    handle(event)
```

Assign the projection once and reuse it. If you need multiple consumers, fan out from one projection in application code.

## Reconnect Exhaustion

Symptoms: runtime errors after repeated stream drops, or messages such as maximum SSE reconnection attempts exceeded.

Facts:

- Shared stream reconnect attempts are limited to 5 by default.
- Lifecycle watcher reconnect attempts are limited to 5 by default.
- Request-level SSE reconnect handling also has a bounded attempt count.

Fixes:

- Treat reconnect exhaustion as a recoverable application-level failure.
- Log sanitized thread/run identifiers, not secrets or full headers.
- Re-open a new stream from the same thread when safe.
- For exactly-once external side effects, coordinate with graph state/checkpoints before retrying. Route persistence-specific design to `persistence`.

## Invalid Input, Config, Or Assistant IDs

Symptoms: command error envelopes such as invalid argument, missing assistant, or server-side validation errors.

Checks:

- `assistant_id` is required for `threads.stream()`.
- `run.start(input=...)` must match the graph's input schema.
- `config` values such as `recursion_limit` must be valid for the graph runtime.
- The assistant must exist on the target server; local assistants are often auto-created from server config, while remote deployments may differ.

Route graph schema and runtime behavior questions to `graph-runtime`.

## Deprecation Or JS SDK Confusion

If JavaScript/TypeScript examples in older material point to this repository, update them to use the public LangGraph.js repository and docs:

- https://github.com/langchain-ai/langgraphjs/tree/main/libs/sdk
- https://docs.langchain.com/oss/javascript/langgraph/overview

Do not invent JS SDK APIs from Python SDK evidence.

## Safe Debug Checklist

Run these before deeper investigation:

```bash
python skills/langgraph/sub-skills/sdk-clients/scripts/inspect_sdk_exports.py --json
python -m pip show langgraph-sdk
```

Then verify a minimal resource call against the intended server with sanitized auth setup. If the minimal call works, debug the specific resource method or stream projection. If it fails, fix installation, URL, server startup, network, or credentials first.
