---
name: connection-and-transport
description: "Configure qdrant-client server and cloud connections, REST versus
  gRPC transport, authentication headers, timeouts, pooling, and connection
  lifecycle without relying on local mode."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Connection and Transport

Use this sub-skill when a task is about constructing a `QdrantClient` or `QdrantRemote` for a running Qdrant server or Qdrant Cloud cluster, choosing REST or gRPC transport, setting URL/host/prefix details, adding authentication, validating timeouts/pooling options, inspecting raw clients, or closing a client cleanly.

Route elsewhere when the task is primarily about:

- `:memory:` or file-backed local storage: use `local-mode`.
- Collection, point, search, query, or payload calls after the client exists: use `client-operations`.
- `AsyncQdrantClient` remote lifecycle and async token-provider details: use `async-client`.
- Cloud inference or embedding model configuration: use `inference`.
- Upload helpers, batch migration, or parallel ingestion: use `migration-and-upload`.
- REST/gRPC model conversion types and generated schemas: use `models-and-conversions`.

## Start Here

1. Choose the address style from `references/connection-reference.md`: `url` for complete endpoints and Qdrant Cloud, or `host` plus `port` for simple server endpoints.
2. Set `check_compatibility=False` only for offline config validation, tests without a server, or startup paths where the background server-version probe is intentionally skipped.
3. Use `prefer_grpc=True` for API methods that support gRPC when low latency or high-throughput server access matters; keep REST as the safe default for full API coverage.
4. Use `api_key` for Qdrant Cloud and API-key deployments. Do not duplicate `api-key` in `headers`; the constructor intentionally overrides that header with `api_key`.
5. Close remote clients with `client.close()` when the process, worker, or request scope ends. Do not reuse a closed client.

## Common Patterns

```python
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")
```

```python
from qdrant_client import QdrantClient

client = QdrantClient(
    url="https://example-cluster.region.cloud.qdrant.io:6333",
    api_key="<qdrant-api-key>",
    headers={"x-trace-id": "request-123"},
)
```

```python
from qdrant_client import QdrantClient

client = QdrantClient(
    host="qdrant.internal",
    port=6333,
    grpc_port=6334,
    prefer_grpc=True,
    timeout=30,
    check_compatibility=False,
)
```

For safe, no-network configuration checks, run the bundled probe:

```bash
python sub-skills/connection-and-transport/scripts/transport_config_probe.py --url http://localhost:6333 --prefix api/v1
```

## Raw Access and Lifecycle

- `client.http` exposes the REST API wrapper for direct REST calls when a high-level method is unavailable.
- `client.grpc_points`, `client.grpc_collections`, `client.grpc_snapshots`, and `client.grpc_root` initialize gRPC channels lazily on first access.
- `client.close()` closes HTTP resources and any initialized gRPC channel pool; accessing remote gRPC after close can raise `RuntimeError`.
- Use one client per process, worker, tenant, or credential scope rather than rebuilding clients for every request.

## References

- `references/connection-reference.md` covers constructor decisions, examples, REST/gRPC selection, authentication, context headers, pooling, raw access, and close lifecycle.
- `references/troubleshooting.md` covers compatibility warnings, insecure auth warnings, prefix conflicts, unsupported gRPC compression, closed clients, pool/limits conflicts, and token-provider pitfalls.
