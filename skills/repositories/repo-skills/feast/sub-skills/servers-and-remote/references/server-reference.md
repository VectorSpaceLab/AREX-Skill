# Server Reference

## Server process chooser

| Task | Command/API | Protocol | Default port | Use when |
|---|---|---:|---:|---|
| Online feature serving | `feast serve` / `FeatureStore.serve(...)` | REST HTTP by default, gRPC via `--type grpc` | `6566` | Serving online features, push writes, materialization triggers, vector document retrieval, chat UI, MCP-mounted endpoints |
| Offline serving | `feast serve_offline` / `FeatureStore.serve_offline(...)` | Arrow Flight (`grpc+tcp` or `grpc+tls`) | `8815` | Delegating historical/offline retrieval to a remote service |
| Registry serving | `feast serve_registry` / `FeatureStore.serve_registry(...)` | gRPC by default, optional REST | gRPC `6570`, REST `6572` | Centralizing registry reads/writes for remote clients and services |
| Transformation serving | `feast serve_transformations` | Feast transformation service | `6569` | Experimental remote transformation consumption |
| MCP-enabled feature server | `feast serve` with `feature_server.type: mcp` and `mcp_enabled: true` | FastAPI plus MCP SSE/HTTP mount | `6566` | Exposing feature-server actions to MCP clients |

Use the underscored CLI names exactly: `serve_offline`, `serve_registry`, and `serve_transformations`. Hyphenated variants such as `serve-offline` are not commands.

## `feast serve` feature server

Typical local command:

```bash
feast --chdir feature_repo serve --host 0.0.0.0 --port 6566 --registry_ttl_sec 60
```

Important options:

- `--type http|grpc`: `http` is the default and exposes the FastAPI routes below; use `grpc` only when clients expect the serving gRPC API.
- `--workers`: worker process count; `-1` auto-calculates from CPU count.
- `--worker-connections`, `--max-requests`, `--max-requests-jitter`, `--keep-alive-timeout`: production tuning knobs passed to the server runtime.
- `--registry_ttl_sec`: refresh interval for the feature-server registry cache; higher values reduce registry overhead but increase staleness.
- `--key` and `--cert`: TLS private key and public cert paths; Feast rejects TLS mode if only one is provided.
- `--metrics`: enables Prometheus metrics server support. `feature_server.metrics.enabled: true` in config can also activate metrics.

Python equivalent from a configured repo:

```python
from feast import FeatureStore

store = FeatureStore(repo_path="feature_repo")
store.serve(
    host="0.0.0.0",
    port=6566,
    type_="http",
    workers=2,
    registry_ttl_sec=60,
    tls_key_path="",
    tls_cert_path="",
)
```

`FeatureStore.serve` signature facts: `host`, `port`, `type_='http'`, `no_access_log=True`, `workers=1`, `worker_connections=1000`, `max_requests=1000`, `max_requests_jitter=50`, `metrics=False`, `keep_alive_timeout=30`, `tls_key_path=''`, `tls_cert_path=''`, `registry_ttl_sec=60`.

## Feature-server REST task routes

The HTTP feature server creates a FastAPI app and exposes task-level routes:

- `GET /health`: checks registry accessibility; expect HTTP `200` when healthy and `503` when registry access fails.
- `POST /get-online-features`: body includes `entities`, either `features` or `feature_service`, plus `full_feature_names` and `include_feature_view_version_metadata` options.
- `POST /retrieve-online-documents`: alpha vector document route; supports vector `query`, `query_string` for API v2, `top_k`, feature refs or feature service.
- `POST /push`: body includes `push_source_name`, tabular `df`, `to` as `online`, `offline`, or `online_and_offline`, and `transform_on_write`.
- `POST /write-to-online-store`: writes a dataframe payload directly to a named feature view in the online store.
- `POST /materialize`: body includes `start_ts`, `end_ts`, optional `feature_views`, `disable_event_timestamp`, and `full_feature_names`.
- `POST /materialize-incremental`: body includes `end_ts`, optional `feature_views`, and `full_feature_names`.
- `GET/POST /chat`, `WS /ws/chat`, and `/static`: simple chat UI and websocket endpoints shipped by the feature server.

Safe health and online examples:

```bash
curl -fsS http://localhost:6566/health
curl -sS -X POST http://localhost:6566/get-online-features \
  -H 'Content-Type: application/json' \
  -d '{"features":["driver_hourly_stats:conv_rate"],"entities":{"driver_id":[1001]}}'
```

If auth is enabled, include `Authorization: Bearer <token>` on REST calls.

## Offline server

Start a remote offline server from the server-side feature repository:

```bash
feast --chdir offline_server/feature_repo apply
feast --chdir offline_server/feature_repo serve_offline --host 0.0.0.0 --port 8815
```

The server listens over Arrow Flight. Without TLS logs should look like `grpc+tcp://host:8815`; with TLS logs should look like `grpc+tls://host:8815`. `FeatureStore.serve_offline(host, port, tls_key_path='', tls_cert_path='')` is the SDK equivalent.

Use this process when clients should call `FeatureStore.get_historical_features(...).to_df()` locally but delegate the offline-store implementation to a remote Feast service via `offline_store: type: remote`.

## Registry server

Start gRPC registry only:

```bash
feast --chdir feature_repo serve_registry --port 6570
```

Start both gRPC and REST registry servers:

```bash
feast --chdir feature_repo serve_registry --port 6570 --rest-api --rest-port 6572
```

Start REST only by disabling gRPC and enabling REST:

```bash
feast --chdir feature_repo serve_registry --no-grpc --rest-api --rest-port 6572
```

`FeatureStore.serve_registry(port, tls_key_path='', tls_cert_path='', rest_api=False)` is the SDK equivalent. The gRPC server exposes registry object CRUD/list APIs, gRPC health, reflection, pagination/sorting, and permission checks. Use it when remote clients or services need a central registry rather than a local registry file.

## TLS mode

Generate development-only self-signed files when needed:

```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes
```

Start servers with both values:

```bash
feast serve --key key.pem --cert cert.pem
feast serve_registry --key key.pem --cert cert.pem
feast serve_offline --key key.pem --cert cert.pem
```

Client-side TLS settings are service-specific:

- Remote online store uses `online_store.cert` to trust a self-signed feature-server certificate.
- Remote registry uses `registry.cert`, and for mTLS can also use `client_cert`, `client_key`, and `authority` for tunnel/proxy hostname verification.
- Remote offline store uses `offline_store.scheme: https` plus `offline_store.cert` for TLS Arrow Flight.
- `FEAST_CA_CERT_FILE_PATH` can point Feast at a CA trust-store path instead of passing individual cert fields.

## MCP server

Enable MCP on the feature server through `feature_server` config, then run `feast serve`:

```yaml
feature_server:
  type: mcp
  enabled: true
  mcp_enabled: true
  mcp_server_name: feast-mcp-server
  mcp_server_version: 1.0.0
  mcp_transport: sse
  transformation_service_endpoint: localhost:6566
```

`mcp_transport` accepts `sse` or `http`. MCP support requires the optional `fastapi_mcp` package; if it is missing, Feast logs that MCP support is disabled and continues running the feature server. If `mcp_transport: http` is selected, the installed `fastapi_mcp` must provide `FastApiMCP.mount_http()`.

## Production topology choices

- Single local dev process: local registry, local offline store, local online store, `feast serve` on loopback.
- Remote online serving: feature server close to the online store; clients configure `online_store: type: remote` or call REST directly.
- Remote offline serving: Arrow Flight offline server close to warehouse credentials/network; clients configure `offline_store: type: remote`.
- Central registry service: `serve_registry` reads/writes registry state for multiple clients and servers; clients configure `registry.registry_type: remote`.
- TLS perimeter: terminate at Feast servers when clients need direct encrypted connections, or terminate upstream at ingress/proxy while preserving service auth headers.
- RBAC topology: run registry, online, and offline services with the same auth model so permission denials are consistent across DESCRIBE, QUERY_OFFLINE, READ_ONLINE, WRITE_ONLINE, and WRITE_OFFLINE operations.
