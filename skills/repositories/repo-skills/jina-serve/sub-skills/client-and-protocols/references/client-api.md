# Client API

## Construction

The installed baseline exposes a convenience `Client` function that selects the correct protocol-specific client class.

Key keyword arguments include:

- `host`
- `port`
- `protocol`
- `asyncio`
- `grpc_channel_options`
- `prefetch`
- `reuse_session`
- `tls`
- `tracing`
- `metrics`
- exporter host/port options for observability

Example:

```python
from jina import Client
client = Client(host="grpc://localhost:12345", protocol="grpc")
```

## `post()` semantics

`Client.post()` and the debugging `Flow.post()` / `Deployment.post()` methods accept the same core signature shape:

- `on`
- `inputs`
- `on_done`
- `on_error`
- `on_always`
- `parameters`
- `target_executor`
- `request_size`
- `continue_on_error`
- `return_responses`
- `max_attempts`
- `initial_backoff`
- `max_backoff`
- `backoff_multiplier`
- `results_in_order`
- `stream`
- `prefetch`
- `return_type`

Use `request_size` to break large iterables into smaller requests. Use `prefetch` to throttle in-flight calls. Use `results_in_order=True` when the caller must preserve stream order.

## Protocol notes

- `grpc` is the default and works well with binary DocArray traffic and streaming semantics.
- `http` is useful for browser/API debugging.
- `websocket` is useful for bidirectional streaming or browser integrations.
- `tls=True` or an `https://`/`wss://`/`grpcs://` style host enables client-side TLS transport when the service is configured for it.

## Parameter routing

Jina can route parameters to specific Executors with namespaced keys such as `executorname__parameter_name`. Use this when multiple Executors in a Flow accept the same parameter names but need distinct values.
