# Async Client Troubleshooting

## Un-Awaited Coroutine

Symptoms:

- `RuntimeWarning: coroutine ... was never awaited`.
- Code prints a coroutine object instead of Qdrant results.
- No collection, point, payload, or query change occurs.

Fix:

- Add `await` before async client operations such as `create_collection`, `upsert`, `query_points`, `query_batch_points`, `set_payload`, `count`, and `close`.
- If the code is not already in an async function, wrap it in `async def main()` and run it with `asyncio.run(main())` in scripts.
- Do not add `await` to `upload_points` or `upload_collection`; those helpers are synchronous on `AsyncQdrantClient`.

## Close Was Not Awaited

Symptoms:

- Warnings about unclosed HTTP clients, gRPC channels, or event-loop resources.
- Persistent local storage remains locked after a script exits abnormally.
- Later use of the same client fails after it was already closed.

Fix:

```python
client = AsyncQdrantClient(url="http://localhost:6333")
try:
    await client.get_collections()
finally:
    await client.close()
```

For web apps, create the client during startup and call `await client.close()` during shutdown. After closing, instantiate a new client rather than reusing the closed one.

## `UnexpectedResponse` or `AioRpcError`

Symptoms:

- REST calls raise `qdrant_client.http.exceptions.UnexpectedResponse`.
- gRPC calls raise `grpc.aio._call.AioRpcError`.
- A collection create call fails because the collection already exists, a server is unreachable, or auth/config differs between REST and gRPC.

Fix:

- For idempotent setup, call `await client.collection_exists(name)` before `create_collection`, or handle the create error and recreate intentionally.
- Verify remote connection settings in the connection-and-transport sub-skill: `url` versus `host`, REST `port`, `grpc_port`, `https`, `api_key`, headers, and `prefer_grpc`.
- If gRPC-only failures appear, retry with `prefer_grpc=False` to isolate transport-specific issues.
- If REST-only failures appear, inspect the server response payload and ensure the API key and URL prefix are correct.
- Set an explicit `timeout` for remote workflows that may otherwise hang behind network or proxy issues.

## Event Loop Misuse

Symptoms:

- `RuntimeError: asyncio.run() cannot be called from a running event loop`.
- Tests or notebooks fail when a helper tries to create its own loop.
- Framework handlers block because sync code wraps async calls incorrectly.

Fix:

- In scripts, use `asyncio.run(main())` only at the top-level entry point.
- Inside notebooks, tests marked with async support, FastAPI/aiohttp handlers, or other running loops, use `await main()` or await the client methods directly.
- Do not call blocking sync wrappers around async client operations from within a running event loop.
- Keep one async client tied to the loop/application lifetime where practical.

## Local Alias Behavior Nuance

Symptoms:

- A local-mode assertion checks `assert await client.get_aliases()` after deleting an alias and passes unexpectedly.
- Remote tests compare `(await client.get_aliases()).aliases == []`, while local tests only assert that a response object exists.

Fix:

- Inspect the response payload, not the truthiness of the response object:

```python
aliases_response = await client.get_aliases()
print(aliases_response.aliases)
```

- For local-mode assertions after deleting an alias, compare the `.aliases` list or look for the specific alias name rather than relying on object truthiness.
- If alias behavior must match production exactly, verify against a server deployment in addition to local mode.

## Snapshot Wait Caveat

Symptoms:

- Snapshot deletion or shard snapshot deletion appears to return before a subsequent list call reflects the deletion.
- A test uses `wait=True` but still needs a short poll or retry before asserting that a shard snapshot disappeared.

Fix:

- Await the snapshot operation, then poll `list_snapshots`, `list_full_snapshots`, or `list_shard_snapshots` until the expected state is visible.
- Treat shard snapshot workflows as server-dependent and avoid using them as deterministic local smoke checks.
- Keep snapshot recovery examples explicit about needing a valid snapshot URL or file URI and a compatible server/storage context.

## Local Storage Lock or Closed Local Client

Symptoms:

- Persistent local path raises a storage-folder already-accessed error.
- Calls fail with a message that the local instance is closed.

Fix:

- Use one active client per persistent local storage directory.
- Always `await client.close()` before opening another client on the same path.
- For concurrent readers/writers, switch to a Qdrant server rather than sharing local storage.

## Raw REST/gRPC Access in Local Mode

Symptoms:

- Accessing `client.http`, `client.grpc_points`, or `client.grpc_collections` raises `NotImplementedError`.

Fix:

- Use high-level methods for code that should work in both local and remote modes.
- Use raw REST/gRPC properties only with a remote `AsyncQdrantClient` and only when transport-specific behavior is required.
