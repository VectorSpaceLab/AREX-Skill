# Connection Reference

This reference distills the qdrant-client 1.18.0 remote connection behavior for `QdrantClient` and its remote backend. It is intentionally self-contained and uses only public constructor patterns.

## Constructor Decision Table

| Need | Constructor shape | Notes |
| --- | --- | --- |
| Default local server over REST | `QdrantClient()` or `QdrantClient(host="localhost", port=6333)` | Creates a remote client for `http://localhost:6333` unless local mode is selected with `":memory:"` or `path=`. |
| Complete endpoint | `QdrantClient(url="http://host:6333")` | `url` wins over the default `port`; include the scheme when you know it. |
| Bare host endpoint | `QdrantClient(host="qdrant.internal", port=6333)` | `host` must not include `http://` or `https://`; use `url` for endpoints with a scheme. |
| Qdrant Cloud or API-key deployment | `QdrantClient(url="https://...:6333", api_key="...")` | Passing `api_key` makes HTTPS the default when `https` is not explicitly set. |
| Reverse proxy path prefix | `QdrantClient(url="https://proxy.example", prefix="api/v1")` | Prefix may be supplied either in `url` path or in `prefix`, but not both. |
| gRPC-preferred calls | `QdrantClient(url="http://host:6333", grpc_port=6334, prefer_grpc=True)` | REST client still exists; gRPC stubs are initialized lazily for supported methods. |
| Offline constructor validation | `QdrantClient(url="http://host:6333", check_compatibility=False)` | Avoids the background server-version compatibility request. It does not prove the server is reachable. |
| Custom bearer token | `QdrantClient(url="https://host:6333", auth_token_provider=get_token)` | Sync clients require a synchronous token provider for sync REST/gRPC usage. |
| HTTP transport tuning | `QdrantClient(url="...", timeout=30, limits=httpx.Limits(...))` | Extra HTTP kwargs are passed into the REST client. Do not combine `limits` with `pool_size`. |
| gRPC transport tuning | `QdrantClient(url="...", prefer_grpc=True, grpc_options={...})` | User-agent is managed by the client; message-size defaults are added when missing. |

Only one remote/local selector should be set among `location`, `url`, `host`, and `path`. Use `":memory:"` or `path=` for local mode, not this sub-skill.

## Address and Prefix Rules

`QdrantClient(url="http://localhost:6333")` produces REST URI `http://localhost:6333`. `QdrantClient(url="localhost:6333")` and `QdrantClient("localhost:6333")` are normalized to HTTP. `QdrantClient("my-domain.com:80")` uses `http://my-domain.com:80`.

`prefix` accepts either `"api/v1"` or `"/api/v1"`; both become `/api/v1` in the REST URI. A trailing slash is preserved, so `"api/v1/"` becomes `/api/v1/`. If the URL already contains a path, such as `url="http://localhost:6333/origin"`, do not also pass `prefix="custom"`.

Use `port=None` when a host string or proxy endpoint should not receive `:6333` automatically:

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="qdrant.internal", port=None, check_compatibility=False)
print(client._client.rest_uri)  # http://qdrant.internal
```

## REST versus gRPC

REST is the default and covers the full API surface. Set `prefer_grpc=True` when you want high-throughput gRPC behavior for supported methods. The remote backend still builds an HTTP/OpenAPI client because compatibility checks, REST-only endpoints, and raw REST access may still need it.

Useful gRPC options:

```python
from grpc import Compression
from qdrant_client import QdrantClient

client = QdrantClient(
    url="http://localhost:6333",
    grpc_port=6334,
    prefer_grpc=True,
    grpc_options={"grpc.max_send_message_length": 64 * 1024 * 1024},
    grpc_compression=Compression.Gzip,
    check_compatibility=False,
)
```

`grpc_options` is also where SSL credential bytes can be supplied for custom secure channels. The SSL option names are `root_certificates`, `private_key`, and `certificate_chain` without a `grpc.` prefix.

## Authentication and Headers

Use `api_key` for Qdrant Cloud or server API-key authentication:

```python
from qdrant_client import QdrantClient

client = QdrantClient(
    url="https://example-cluster.region.cloud.qdrant.io:6333",
    api_key="<qdrant-api-key>",
    headers={"x-tenant": "analytics"},
)
```

The constructor adds `api-key` to REST headers and gRPC metadata. If `headers` already contains `api-key`, the explicit `api_key` argument overrides it and emits a warning. Prefer this shape to avoid accidental duplicate or stale API keys.

Use `auth_token_provider` when the server expects bearer auth:

```python
from qdrant_client import QdrantClient


def get_token() -> str:
    return "fresh-token"

client = QdrantClient(
    url="https://qdrant.example.com:6333",
    auth_token_provider=get_token,
)
```

For a synchronous `QdrantClient`, the token provider must be synchronous for sync REST and gRPC calls. Use `AsyncQdrantClient` for async token-provider workflows.

For per-call contextual headers, use the public context manager:

```python
from qdrant_client import QdrantClient
from qdrant_client.context_headers import headers

client = QdrantClient(url="https://qdrant.example.com:6333", api_key="<key>")

with headers({"x-request-id": "req-42"}):
    client.get_collections()
```

Context headers are added to both REST middleware and gRPC interceptors.

## Timeout, Pooling, and HTTP kwargs

`timeout` is rounded up to an integer and applied to the REST client; when omitted, the default gRPC timeout is used internally. Extra keyword arguments are passed to the REST/OpenAPI client, including `http2`, `verify`, proxies, and HTTPX `limits`.

`pool_size` affects the gRPC channel pool and, for non-local HTTP endpoints without explicit `limits`, can also become the HTTP max-connections setting. If you need exact HTTPX limits, pass `limits=httpx.Limits(...)` and omit `pool_size`.

For `localhost` and `127.0.0.1`, the remote backend disables HTTP keep-alive by default to avoid local delay patterns.

## Raw Client Access

After constructing a public `QdrantClient`, these accessors are useful for advanced transport tasks:

- `client.http` for the REST/OpenAPI wrapper.
- `client.grpc_points` for point service stubs.
- `client.grpc_collections` for collection service stubs.
- `client.grpc_snapshots` for snapshot service stubs.
- `client.grpc_root` for root/service-level gRPC stubs.

Raw gRPC access initializes channels lazily. If the client was closed before gRPC initialization, gRPC initialization raises `RuntimeError`.

## Close Lifecycle

Call `client.close()` to close the REST/OpenAPI client and any initialized gRPC channels. Closed clients should be discarded. Create a new `QdrantClient` instead of trying to reopen or reuse one.

```python
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333", check_compatibility=False)
try:
    print(client.http)
finally:
    client.close()
```

## Offline Transport Probe

The bundled `scripts/transport_config_probe.py` script builds clients with `check_compatibility=False`, prints the resolved REST URI and selected transport flags, and closes the client. It is safe for address-shape validation because it does not intentionally call server APIs. It cannot validate credentials, server availability, API compatibility, or network firewalls.
