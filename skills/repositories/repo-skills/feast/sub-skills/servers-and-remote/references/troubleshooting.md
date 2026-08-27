# Troubleshooting Servers and Remote Stores

## Start with a safe smoke check

Run the bundled helper before launching long-running servers:

```bash
python scripts/server_smoke_check.py --repo-path feature_repo --command serve
python scripts/server_smoke_check.py --repo-path feature_repo --command serve_registry --tls
python scripts/server_smoke_check.py --repo-path feature_repo --command serve_offline --print-curl
```

By default the script checks `feast` availability, parses command choices, validates obvious config/cert paths, and prints next steps. It does not start a server unless `--run` is explicit.

## Install, import, and optional extras

Signals:

- `feast: command not found`: the Feast CLI entry point is not installed or the wrong environment is active.
- `ModuleNotFoundError: feast`: Python cannot import the installed package.
- `fastapi_mcp is not installed`: MCP was requested but optional MCP dependency support is absent; install the MCP extra or disable MCP config.
- `ImportError` for `pyarrow.flight`, `grpc`, FastAPI, or auth libraries: the server path needs an installation with relevant serving dependencies.

Checks:

```bash
feast version
feast --help
python - <<'PY'
import feast
print(feast.__version__)
PY
```

If the CLI works but Python import fails, compare `which feast` with the Python interpreter used by the agent or service manager.

## CLI misuse

Signals and fixes:

- `No such command 'serve-offline'. Did you mean 'serve_offline'?`: use `serve_offline`.
- `No such command 'serve-registry'. Did you mean 'serve_registry'?`: use `serve_registry`.
- TLS startup error requiring `--cert` and `--key`: pass both files or neither.
- Server starts against the wrong repo: use `feast --chdir feature_repo ...` or run from the directory containing `feature_store.yaml`.
- Feature server serves stale definitions: lower `--registry_ttl_sec` or trigger a restart after `feast apply`; higher TTL reduces registry overhead but increases staleness.

## Config and data validation

Signals:

- `/health` returns `503`: the feature server cannot list registry projects; check registry path, remote registry reachability, credentials, and applied project state.
- `FeatureViewNotFoundException`, missing feature service, or missing feature ref: requested object was not applied, uses the wrong project, or is misnamed.
- Online response statuses include `NOT_FOUND`, `NULL_VALUE`, or `OUTSIDE_MAX_AGE`: retrieval reached the online store but data is absent, null, or outside TTL.
- Materialization endpoints reject timestamps: `/materialize` needs both `start_ts` and `end_ts` unless `disable_event_timestamp` is true.
- `/push` rejects `to`: allowed values are `online`, `offline`, and `online_and_offline`.

Fix path:

1. Validate repo config and apply state with the feature-repo/CLI sub-skill.
2. Confirm feature definitions and feature refs with the feature-definitions sub-skill.
3. Confirm materialization and online/offline retrieval semantics with the retrieval-and-materialization sub-skill.
4. Return here for server-specific network/TLS/auth issues.

## Network and port issues

Signals:

- `Connection refused`: process is not running, port is wrong, host binds only to loopback, or firewall/ingress blocks the route.
- Client hangs or times out: service DNS resolves but backend is unreachable, TLS handshake stalls, or proxy/ingress misroutes protocol.
- Arrow Flight errors from remote offline store: host/port/scheme mismatch, offline server down, TLS mismatch, or missing Arrow Flight dependency.
- gRPC registry health/reflection unavailable: registry server not listening on the configured port or started REST-only.

Checks:

```bash
curl -fsS http://localhost:6566/health
nc -vz localhost 6570
nc -vz localhost 8815
```

Use `https://` and the proper CA cert when TLS is enabled.

## TLS failures

Signals:

- Server refuses to start: only `--key` or only `--cert` was supplied.
- `CERTIFICATE_VERIFY_FAILED`: client does not trust the server certificate; set the service-specific `cert` field or `FEAST_CA_CERT_FILE_PATH`.
- Hostname mismatch through a tunnel: remote registry certificate is issued for the service hostname but client connects to `localhost`; set registry `authority` to the service hostname.
- Offline TLS still fails after adding `cert`: ensure `offline_store.scheme: https`; default scheme is `http`.

Safe dev certificate command:

```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes
```

Production guidance: use trusted CA-issued certificates or a managed internal CA, not ad-hoc self-signed files.

## Auth and RBAC failures

Use this matrix before changing feature definitions:

| Symptom | Likely cause | Next check |
|---|---|---|
| 401 or unauthenticated | Missing/expired/malformed token | Confirm `Authorization: Bearer ...`, `LOCAL_K8S_TOKEN`, or configured `user_token` |
| 403 or permission denied | Token parsed, but policy denies action | Check `Permission` actions and user role/group/namespace claims |
| DESCRIBE/list works, online read denied | User has metadata read but lacks `READ_ONLINE` | Add/read `READ_ONLINE` permission for requested feature views/service |
| Historical retrieval denied | Missing `QUERY_OFFLINE` | Check feature view/service offline permission |
| Materialization denied | Missing `WRITE_ONLINE` | Check selected feature views and write permissions |
| Push offline denied | Missing `WRITE_OFFLINE` or both actions for `online_and_offline` | Check `/push` `to` value and matching permission actions |
| Feature view not found | Object/config issue, not RBAC | Confirm project, `feast apply`, exact feature-view name, and registry target |

For Kubernetes auth, verify the Kubernetes `Role`, `RoleBinding`, service account, group, namespace, and token claims match Feast `Permission` policies. For OIDC, verify issuer/client config and role/group claims in the token.

## Backend and service credentials

Remote topology moves where credentials must exist:

- Feature server needs online-store credentials and registry access.
- Offline server needs warehouse/offline-store credentials and registry access.
- Registry server needs registry backend credentials.
- Clients using remote stores need server reachability, auth tokens, and TLS trust, but should not need direct warehouse or online-store credentials unless they also run local retrieval paths.

Signals:

- Feature server starts but `/get-online-features` returns backend errors: online-store credentials or network are missing on the server host.
- Offline server accepts connections but historical retrieval fails: warehouse credentials/data-source access are missing on the offline server host.
- Registry server starts but object operations fail: registry backend path or object-store credentials are wrong.

## Difficult case playbooks

### TLS registry plus Python feature server

1. Server side: run `feast apply`, then `feast serve_registry --key key.pem --cert cert.pem --port 6570`.
2. Client/server config: set `registry.registry_type: remote`, `registry.path: host:6570`, and `registry.cert: /path/to/ca.crt`.
3. Feature server side: point the feature-server repo config at that remote registry, then run `feast serve --host 0.0.0.0 --port 6566 --registry_ttl_sec 60` with TLS only if clients call it directly over HTTPS.
4. Validate: `curl /health` for feature server and a registry list/apply command from a client using the remote registry config.

### 401/403 versus missing feature view

1. Repeat the exact request with a known admin token. If admin succeeds and user fails, focus on RBAC.
2. If admin also sees missing feature view/service, focus on project mismatch, unapplied registry, or incorrect feature ref.
3. If no token gets past the server, focus on auth config, token parser, bearer header, or Kubernetes/OIDC setup.
4. If metadata calls work but retrieval fails, inspect action-specific permissions: `READ_ONLINE`, `QUERY_OFFLINE`, `WRITE_ONLINE`, or `WRITE_OFFLINE`.
