# Remote Stores

Remote stores let a Feast client keep the normal `FeatureStore` API while delegating registry, online, or offline work to Feast server processes.

## Remote registry

Client config for a gRPC registry server:

```yaml
project: feast_project
provider: local
registry:
  registry_type: remote
  path: localhost:6570
online_store:
  type: sqlite
  path: data/online_store.db
entity_key_serialization_version: 3
auth:
  type: no_auth
```

TLS remote registry with optional mTLS and proxy/tunnel authority:

```yaml
registry:
  registry_type: remote
  path: feature-registry.example.com:443
  cert: /path/to/ca.crt
  client_cert: /path/to/tls.crt
  client_key: /path/to/tls.key
  authority: feature-registry.example.com
```

Use `authority` when the client connects through `localhost` or a tunnel but the server certificate is issued for the real service hostname.

Server command:

```bash
feast --chdir feature_repo serve_registry --port 6570 --rest-api --rest-port 6572
```

Notes:

- gRPC registry is enabled by default.
- REST registry is opt-in with `--rest-api`.
- `--no-grpc --rest-api` starts REST without the gRPC registry process.
- Registry server enforces auth/RBAC when `auth.type` is not `no_auth`.

## Remote online store

Client config for a remote feature server:

```yaml
project: feast_project
provider: local
registry:
  registry_type: remote
  path: localhost:6570
online_store:
  type: remote
  path: http://localhost:6566
entity_key_serialization_version: 3
auth:
  type: no_auth
```

TLS remote online store:

```yaml
online_store:
  type: remote
  path: https://feature-server.example.com:6566
  cert: /path/to/ca.crt
  connection_pool_size: 50
  connection_idle_timeout: 300
  connection_retries: 3
```

Server command:

```bash
feast --chdir feature_repo serve --host 0.0.0.0 --port 6566 --registry_ttl_sec 60
```

The remote online store wraps feature-server REST calls for online retrieval, online writes, and vector document retrieval. It preserves client-facing calls such as `FeatureStore.get_online_features(...)`, but the actual online read goes to `/get-online-features` on the feature server.

## Remote offline store

Client config for a remote Arrow Flight offline server:

```yaml
project: feast_project
provider: local
registry:
  registry_type: remote
  path: localhost:6570
offline_store:
  type: remote
  host: localhost
  port: 8815
entity_key_serialization_version: 3
auth:
  type: no_auth
```

TLS remote offline store:

```yaml
offline_store:
  type: remote
  host: offline-server.example.com
  port: 8815
  scheme: https
  cert: /path/to/ca.crt
  connection_retries: 3
```

Server command:

```bash
feast --chdir offline_server/feature_repo serve_offline --host 0.0.0.0 --port 8815
```

The remote offline store delegates historical retrieval, validation, persistence, and offline write paths to the offline server. Client code can still call `FeatureStore.get_historical_features(...).to_df()`; if the client sees Arrow Flight connection errors, verify the offline server is reachable and that `scheme: https` matches TLS mode.

## Combined production layout

A common production topology separates client config from server config:

- Registry server owns registry access and permission-protected object APIs.
- Feature server runs near the online store and exposes low-latency online read/write routes.
- Offline server runs near the warehouse or batch data network and exposes Arrow Flight retrieval.
- Clients point `registry`, `online_store`, and `offline_store` to remote services and supply the same `auth` strategy.

Example client config:

```yaml
project: feast_project
provider: local
registry:
  registry_type: remote
  path: registry.internal:6570
online_store:
  type: remote
  path: https://online.internal:6566
  cert: /etc/feast/ca.crt
offline_store:
  type: remote
  host: offline.internal
  port: 8815
  scheme: https
  cert: /etc/feast/ca.crt
entity_key_serialization_version: 3
auth:
  type: kubernetes
```

## Config validation checklist

- The client `project` matches the server-side applied project.
- The server-side feature repo has run `feast apply` before clients retrieve or list registry objects.
- Client remote URLs use `http`/`https` for online feature server paths and host/port/scheme fields for remote offline store.
- TLS client `cert` points to a CA/public cert that can validate the server certificate.
- Remote registry `path` uses the form expected by the registry client, commonly `host:port` for gRPC.
- Auth config is compatible across all services; `no_auth` mixed with OIDC/Kubernetes can create confusing allow/deny differences.
- Backend credentials are available where the actual work runs: online-store credentials on the feature server, warehouse/offline-store credentials on the offline server, registry credentials on the registry server.
