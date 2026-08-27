# Configuration

Use this reference when you need to audit or change Xinference runtime knobs
before a rollout. It focuses on state, exposure, observability, and launch
safety rather than model-family or request-body details.

## Connection default

| Variable | Default | Meaning |
| --- | --- | --- |
| `XINFERENCE_ENDPOINT` | `http://127.0.0.1:9997` | Client-side default endpoint for tools and SDKs. |

## Persistent state and caches

| Variable | Default | Meaning |
| --- | --- | --- |
| `XINFERENCE_HOME` | `~/.xinference` | Base directory for logs, auth state, model caches, and other persisted data. |
| `XINFERENCE_LOG_DIR` | `<XINFERENCE_HOME>/logs` | Log directory used by application and audit logs. |
| `XINFERENCE_AUTH_DB_PATH` | `<XINFERENCE_HOME>/auth/auth.db` | SQLite database for users, permissions, API keys, and refresh tokens. |
| `XINFERENCE_LAUNCH_HISTORY_DB_PATH` | `<XINFERENCE_HOME>/launch_history.db` | Web UI launch-history store. |
| `XINFERENCE_MONITOR_CONFIG_DB_PATH` | `<XINFERENCE_HOME>/monitor_config.db` | Persisted monitoring configuration store. |

`XINFERENCE_HOME` is the anchor for the rest of the persisted layout. When it
changes, the process also points its model-download caches at subdirectories
under that home so model artifacts stay writable and reusable across restarts.
If `XINFERENCE_AUTH_JWT_SECRET_KEY` or `XINFERENCE_AUTH_ENCRYPTION_KEY` is
unset, Xinference generates and persists the corresponding secret under
`<XINFERENCE_HOME>/auth/` on first run.

## Model source and downloads

| Variable | Default | Meaning |
| --- | --- | --- |
| `XINFERENCE_MODEL_SRC` | `huggingface` | Model hub to use for built-ins; `modelscope` is the alternate documented source. |
| `XINFERENCE_CSG_TOKEN` | unset | Authentication token for CSGHub model downloads. |
| `XINFERENCE_CSG_ENDPOINT` | `https://hub-stg.opencsg.com/` | CSGHub endpoint used for model source access. |
| `XINFERENCE_MODEL_DOWNLOAD_WORKERS` | `2` | Parallel download worker count for model files. |
| `XINFERENCE_DOWNLOAD_MAX_ATTEMPTS` | `3` | Retry budget for failed model downloads. |
| `XINFERENCE_TRUST_REMOTE_CODE` | off | Allow models to execute their own remote code; leave off unless you trust the source. |

## Health, metrics, logging, and request safety

| Variable | Default | Meaning |
| --- | --- | --- |
| `XINFERENCE_HEALTH_CHECK_FAILURE_THRESHOLD` | `5` | Failed health checks tolerated at startup. |
| `XINFERENCE_HEALTH_CHECK_INTERVAL` | `5` | Seconds between startup health checks. |
| `XINFERENCE_HEALTH_CHECK_TIMEOUT` | `10` | Seconds allowed for each startup health check. |
| `XINFERENCE_DISABLE_HEALTH_CHECK` | off | Disable startup health checks entirely. |
| `XINFERENCE_DISABLE_METRICS` | off | Remove the `/metrics` endpoint on the supervisor and stop the worker metrics server. |
| `XINFERENCE_HTTP_REQUEST_TIMEOUT` | `120` | Seconds allowed to receive a full HTTP request body; protects against slow-request abuse. |
| `XINFERENCE_HTTP_TIMEOUT_KEEP_ALIVE` | `5` | Idle keep-alive timeout between requests. |
| `XINFERENCE_HTTP_LIMIT_CONCURRENCY` | unset | Cap concurrent requests; unset means unlimited. |
| `XINFERENCE_TCP_REQUEST_TIMEOUT` | `5` | TCP request timeout used for internal request handling. |
| `XINFERENCE_SSE_PING_ATTEMPTS_SECONDS` | `600` | Server-sent-events keepalive ping interval. |
| `XINFERENCE_LOG_CONSOLE` | `true` | Mirror logs to console; set false for file-only logging. |
| `XINFERENCE_LOG_FORMAT` | `text` | Log format: `text` or `json`. |
| `XINFERENCE_LOG_DOWNLOAD_PROGRESS` | `sampled` | How download progress is logged when console logging is off. |
| `XINFERENCE_LOG_ROTATION` | `daily+size` | Log rotation mode. |
| `XINFERENCE_LOG_RETENTION_DAYS` | `30` | Log retention window. |
| `XINFERENCE_LOG_MAX_BYTES` | `104857600` | Maximum log size per file. |
| `XINFERENCE_LOG_BACKUP_COUNT` | `300` | Number of retained rotated log files. |

Notes:
- Metrics are on by default; `XINFERENCE_DISABLE_METRICS=1` turns the feature
  off rather than merely hiding it.
- CORS is permissive in the server middleware, so origin checks are not an
  access-control boundary.
- For observability beyond Prometheus, see the optional OpenTelemetry section
  in `references/metrics-and-observability.md`.

## Launch and concurrency

| Variable | Default | Meaning |
| --- | --- | --- |
| `XINFERENCE_MAX_TOKENS` | unset | Global max-token cap override for requests. |
| `XINFERENCE_BATCH_SIZE` | `32` | Batch size used when batching is enabled. |
| `XINFERENCE_BATCH_INTERVAL` | `0.003` | Default batching interval in seconds. |
| `XINFERENCE_ALLOW_MULTI_REPLICA_PER_GPU` | `1` | Permit multiple replicas to share a GPU. |
| `XINFERENCE_LAUNCH_STRATEGY` | `IDLE_FIRST_LAUNCH_STRATEGY` | GPU allocation strategy for replicas. |
| `XINFERENCE_MAX_CONCURRENT_LAUNCHES` | `5` | Maximum concurrent model launches per worker. |
| `XINFERENCE_STATUS_GATHER_TIMEOUT` | `10` | Seconds allowed for status collection. |
| `XINFERENCE_STATUS_REPORT_MULTIPLIER` | `3` | Heartbeat multiplier for full status reports. |
| `XINFERENCE_LIST_MODELS_PER_WORKER_TIMEOUT` | `60` | Per-worker timeout for list-models RPCs. |
| `XINFERENCE_LIST_MODELS_DEBOUNCE_SECONDS` | `3` | Debounce window for repeated list-models refreshes. |
| `XINFERENCE_MODEL_ACTOR_AUTO_RECOVER_LIMIT` | unset | Limit on automatic actor recovery attempts. |
| `XINFERENCE_TEXT_TO_IMAGE_BATCHING_SIZE` | unset | Enable text-to-image continuous batching by image size. |

## Frontend static serving

| Variable | Default | Meaning |
| --- | --- | --- |
| `XINFERENCE_FRONTEND_DIST_DIR` | unset | Path to a static Web UI export to serve instead of the bundled export. |

## Auth, OIDC, audit, and network exposure

| Variable | Default | Meaning |
| --- | --- | --- |
| `XINFERENCE_AUTH_ADVANCED` | `1` | Enable database-backed authentication; set false only for intentionally open deployments. |
| `XINFERENCE_AUTH_DB_PATH` | `<XINFERENCE_HOME>/auth/auth.db` | User, permission, API-key, and refresh-token database. |
| `XINFERENCE_AUTH_JWT_SECRET_KEY` | auto-generated | JWT signing secret, persisted on first run if unset. |
| `XINFERENCE_AUTH_ENCRYPTION_KEY` | auto-generated | Secret used to encrypt stored API keys, persisted on first run if unset. |
| `XINFERENCE_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access-token lifetime in minutes. |
| `XINFERENCE_PASSWORD_MIN_LENGTH` | `8` | Minimum password length enforced by login and reset flows. |
| `XINFERENCE_OIDC_ENABLED` | `0` | Enable OIDC single sign-on. |
| `XINFERENCE_OIDC_ISSUER` | unset | OIDC issuer URL. |
| `XINFERENCE_OIDC_CLIENT_ID` | unset | OIDC client ID. |
| `XINFERENCE_OIDC_CLIENT_SECRET` | unset | OIDC client secret for the confidential client. |
| `XINFERENCE_OIDC_REDIRECT_URI` | unset | OIDC callback URL back to Xinference. |
| `XINFERENCE_AUDIT_LOG_RETENTION_DAYS` | `90` | Audit-log retention window. |
| `XINFERENCE_AUDIT_ES_INDEX` | `xinference-audit-*` | Elasticsearch index pattern for audit searches. |
| `XINFERENCE_RATE_LIMIT_IP_MAX_FAILURES` | `10` | Invalid-key attempts allowed per IP before ban. |
| `XINFERENCE_RATE_LIMIT_IP_WINDOW_SECONDS` | `300` | IP failure window. |
| `XINFERENCE_RATE_LIMIT_IP_BAN_SECONDS` | `3600` | IP ban duration. |
| `XINFERENCE_RATE_LIMIT_KEY_MAX_FAILURES` | `5` | Invalid-key attempts allowed per (IP, key). |
| `XINFERENCE_RATE_LIMIT_KEY_WINDOW_SECONDS` | `300` | Key failure window. |
| `XINFERENCE_RATE_LIMIT_KEY_BAN_SECONDS` | `3600` | Key ban duration. |
| `XINFERENCE_ALLOWED_IPS` | unset | Restrict access to selected IPs or CIDR blocks. |
| `XINFERENCE_TRUSTED_PROXIES` | unset | Only honor forwarded IP headers from these proxy peers. |
| `XINFERENCE_ES_URL` | unset | Point audit search and related admin views at Elasticsearch. |

## Virtual env behavior

| Variable | Default | Meaning |
| --- | --- | --- |
| `XINFERENCE_ENABLE_VIRTUAL_ENV` | `1` | Enable per-model virtual environments. |
| `XINFERENCE_VIRTUAL_ENV_SKIP_INSTALLED` | `1` | Skip packages already present in system site-packages. |
| `XINFERENCE_VIRTUAL_ENV_OFFLINE_INSTALL` | `0` | Force offline wheel-only installation behavior for virtual envs. |

## Quick operator rule of thumb

- Use the helper script for a categorized dump of the same matrix.
- Change persistence and auth variables together so the deployment keeps using
the same secrets after restart.
- Treat IP restrictions, trusted proxies, and permissive CORS as separate
controls: they solve different problems.
