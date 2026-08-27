# HTTP Client Reference

## Constructors

Verified public client signatures:

```python
bentoml.SyncHTTPClient(url, *, token=None, timeout=30, server_ready_timeout=None)
bentoml.AsyncHTTPClient(url, *, token=None, timeout=30, server_ready_timeout=None)
```

Implementation-supported keyword arguments also include `media_type`, `service`, and `app`; reserve these for advanced/internal testing because common user workflows only need URL, auth token, timeout, and readiness timeout.

The client sends `User-Agent: BentoML HTTP Client/<version>`. If `token` is provided, or if `BENTO_CLOUD_API_KEY` is set and `token` is omitted, it sends `Authorization: Bearer <token>`.

## Schema Discovery

When constructed against a URL, the client:

1. Waits for `/readyz` unless readiness waiting is disabled.
2. Fetches `/schema.json`.
3. Registers one endpoint per schema route.
4. Creates dynamic endpoint methods and supports `client.call(name, *args, **kwargs)`.

Useful manual inspection endpoints:

- `GET /readyz` returns `200` when the service is ready.
- `GET /schema.json` returns client-facing routes with endpoint `name`, HTTP `route`, `input`, `output`, `doc`, stream flag, and task flag.
- The browser UI is available at the server root and OpenAPI JSON is available from the docs route as `docs.json`.

## Synchronous Calls

```python
import bentoml

with bentoml.SyncHTTPClient("http://localhost:3000", server_ready_timeout=60) as client:
    if client.is_ready():
        result = client.summarize(text="long text")
        print(result)
```

Use `client.call()` for dynamic names:

```python
with bentoml.SyncHTTPClient("http://localhost:3000") as client:
    result = client.call("summarize", text="long text")
```

## Asynchronous Calls

```python
import asyncio
import bentoml

async def main() -> None:
    async with bentoml.AsyncHTTPClient("http://localhost:3000", server_ready_timeout=60) as client:
        result = await client.summarize(text="long text")
        print(result)

asyncio.run(main())
```

Always close async clients with `async with` or `await client.close()`.

## Argument Shape Rules

- For normal structured APIs, pass exactly the endpoint’s named parameters: `client.encode(sentences=["a", "b"])`.
- Positional arguments map to schema property order, but keyword arguments are clearer.
- Duplicate positional and keyword values raise `TypeError`.
- Unknown kwargs raise `TypeError` with `Arguments not found in endpoint ...`.
- Missing required kwargs raise `TypeError` with `Missing required arguments in endpoint ...`.
- Root-input APIs accept exactly one positional argument and no kwargs.
- File fields are sent as multipart by the client when the schema marks a property as a file or an array of files.

Root-input example:

```python
with bentoml.SyncHTTPClient("http://localhost:3000") as client:
    result = client.classify([5.1, 3.5, 1.4, 0.2])
```

Structured-input example:

```python
with bentoml.SyncHTTPClient("http://localhost:3000") as client:
    result = client.classify(features=[5.1, 3.5, 1.4, 0.2])
```

## Streaming Outputs

When an endpoint output schema has `is_stream`, the sync client returns an iterator and the async client returns an async stream parser.

```python
with bentoml.SyncHTTPClient("http://localhost:3000") as client:
    for chunk in client.generate(prompt="hello"):
        print(chunk, end="")
```

```python
async with bentoml.AsyncHTTPClient("http://localhost:3000") as client:
    stream = await client.generate(prompt="hello")
    async for chunk in stream:
        print(chunk, end="")
```

If the exact async streaming return style is uncertain for a custom endpoint, inspect `/schema.json` first and test with a small prompt.

## Raw Requests

Both clients expose the underlying HTTPX request method for non-generated routes such as custom ASGI routes:

```python
with bentoml.SyncHTTPClient("http://localhost:3000") as client:
    response = client.request("GET", "/readyz")
    print(response.status_code)
```

For WebSockets, do not use BentoML’s HTTP client; use a WebSocket library and the mounted ASGI route.
