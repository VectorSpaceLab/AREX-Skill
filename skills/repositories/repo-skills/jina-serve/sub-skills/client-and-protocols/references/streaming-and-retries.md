# Streaming, Callbacks, and Retries

## Streaming and async clients

Use a generator or async generator as `inputs` when you want to stream documents progressively.

```python
from jina import Client
from docarray import BaseDoc

async_client = Client(host="grpc://localhost:12345", asyncio=True)
```

The async client returns an async iterator for streamed responses.

## Callbacks

- `on_done` runs for successful streamed responses.
- `on_error` runs when the request gets an executor-level error.
- `on_always` runs regardless of success or failure in the stream.

Callbacks observe `Response` / `DataRequest` objects rather than raw documents.

## Retries

Jina client request retry knobs:

- `max_attempts`
- `initial_backoff`
- `max_backoff`
- `backoff_multiplier`

Use these for transient gRPC/HTTP/WebSocket transport errors. If the callable input is a generator, be careful to keep the stream consumable across retries.

## Targeting specific Executors

Use `target_executor="name*"` or an exact Executor name to send a request only to matching Executor nodes inside a Flow. This is different from endpoint routing; it chooses which Executor instances receive the request.
