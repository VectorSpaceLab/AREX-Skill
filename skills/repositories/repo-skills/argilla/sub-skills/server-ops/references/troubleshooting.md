# Argilla server troubleshooting

Use this reference after checking the deployment path and CLI/config reference. The safest first checks are help rendering, Compose config rendering, and logs; do not start, migrate, reindex, or change credentials without user approval.

## Fast triage checklist

1. Identify deployment path: HF Space, Docker Compose, direct Python, or Kubernetes.
2. Confirm version and package import with `python scripts/check_server_cli.py --group root`.
3. Render help with `python scripts/check_server_cli.py --group all`; if help fails, fix the Python dependency issue before debugging services.
4. Check required service endpoints: DB, search engine, Redis, and any proxy/base URL.
5. For Docker/Compose, validate config and inspect logs before recreating volumes.
6. For search symptoms after an upgrade or migration, plan a reindex rather than changing dataset code.

## Symptom-to-fix table

| Symptom | Likely cause | Checks | Recovery |
| --- | --- | --- | --- |
| `python -m argilla_server --help` fails with `TypeError: Secondary flag is not valid for non-boolean flag`. | Typer 0.9.x and newest Click are incompatible. A fresh resolver can also pull Hub libraries outside the known-good range. | `python -m pip show typer click huggingface-hub`; render CLI help only. | Pin `click<8.2`. For Argilla 2.8.0dev0, a working inspected set used Click 8.1.x and `huggingface-hub<1.0`. Re-run help before starting services. |
| Server startup says search engine is not available or not responding. | `ARGILLA_ELASTICSEARCH` wrong, search container not ready, wrong `ARGILLA_SEARCH_ENGINE`, TLS/CA mismatch, unsupported version, or auth/security mismatch. | Logs for server and search engine; `ARGILLA_SEARCH_ENGINE`; endpoint URL; Elasticsearch >= 8.5.0 or OpenSearch >= 2.4.0; TLS variables. | Start/fix search engine, set correct endpoint, choose `elasticsearch` or `opensearch`, set `ARGILLA_ELASTICSEARCH_SSL_VERIFY`/`ARGILLA_ELASTICSEARCH_CA_PATH`, restart server. |
| UI loads but search/filtering/vector similarity is empty, stale, or broken after upgrade/migration. | Search index is stale or missing. | Server logs; search-engine logs; dataset count; whether `REINDEX_DATASETS` was set only for startup. | Run `python -m argilla_server search-engine reindex` or set `REINDEX_DATASETS=1` for one intentional Docker startup. Use `--dataset-id <uuid>` for a targeted rebuild. |
| Server fails during DB setup or schema mismatch appears. | Migrations not run, wrong DB URL/driver, PostgreSQL optional driver missing, SQLite volume not persistent, or locked SQLite DB. | `ARGILLA_DATABASE_URL`; `python -m argilla_server database revisions`; DB service logs; SQLite file path under `ARGILLA_HOME_PATH`. | Backup first, then run `python -m argilla_server database migrate --revision head`. Use `postgresql+asyncpg://...` for PostgreSQL and install async driver support if needed. For SQLite locks, reduce concurrency or raise timeout. |
| Data disappears after HF Space restart or settings change. | Space was using ephemeral storage. | HF Space storage setting; Argilla persistent storage warning; exported dataset/user backups. | For non-test use, enable persistent storage before relying on the Space. If enabling after data exists, export datasets/users first because changing storage restarts the Space and can lose existing local data. |
| Private HF Space returns 401/403 to SDK. | Confusing the HF token with the Argilla API key, missing `Authorization` header, or Space visibility/access mismatch. | Try browser access with same HF identity; verify SDK has `headers={"Authorization": "Bearer <hf-token>"}` and `api_key="<argilla-api-key>"`. | Use both credentials: HF token as `Authorization` bearer header for private Space access, Argilla API key for Argilla API auth. Retrieve/rotate the Argilla API key in the Space UI if needed. |
| OAuth redirects fail, return unauthorized, or loop. | Redirect URI mismatch, HTTP redirect blocked, wrong OAuth config path/name, missing provider env vars, proxy/base URL mismatch, or cookies over HTTP. | `ARGILLA_AUTH_OAUTH_CFG`; `.oauth.yaml` content; provider app redirect URI; `ARGILLA_BASE_URL`; external URL; forwarded headers; `allow_http_redirect`. | Use HTTPS and redirect URI `https://host[/base]/oauth/<provider>/callback`. Set `ARGILLA_BASE_URL` for prefix deployments. Use `allow_http_redirect: true` only for local tests. |
| Users cannot access expected workspaces after OAuth login. | `allowed_workspaces` list is too narrow, workspace naming mismatch, or Keycloak roles/workspaces not mapped. | OAuth YAML; server startup logs; user role; Keycloak realm roles if used. | Add intended workspaces to `allowed_workspaces`, ensure names match, restart server. For Keycloak, provide roles like `argilla_role:annotator` and `argilla_workspace:<workspace>`. |
| Logged-in sessions/API tokens become invalid after restart or across replicas. | `ARGILLA_AUTH_SECRET_KEY` was random per process. | Environment across server replicas/containers; restart history. | Set one stable secret key for every server instance and keep it across restarts. Rotate intentionally with expected session invalidation. |
| Redis errors at startup or workers do nothing. | Redis not reachable, wrong URL/db, cluster mode mismatch, worker using different env from server. | Server logs; worker logs; `ARGILLA_REDIS_URL`; `ARGILLA_REDIS_USE_CLUSTER`; Redis container status. | Fix Redis endpoint, align server and worker env, start workers with `python -m argilla_server worker --num-workers 2`. |
| Docker server exits immediately or keeps restarting. | One dependency not healthy, credentials invalid, migrations fail, search engine memory/security issue, or wrong env interpolation. | `docker compose config`; `docker compose ps`; `docker compose logs -f argilla worker elasticsearch postgres redis`; volumes. | Fix first failing dependency. For local Elasticsearch, ensure sufficient memory and security disabled only in private local samples. Do not delete volumes unless the user accepts data loss. |
| Proxy deployment shows broken static assets, `/api` paths, or login callback under the wrong path. | `ARGILLA_BASE_URL` and proxy strip/prefix behavior disagree. | Browser network paths; server logs; proxy config; public URL prefix. | Set `ARGILLA_BASE_URL=/prefix`; align proxy route/strip behavior; preserve Host and `X-Forwarded-*` headers; update SDK `api_url` and OAuth redirect URI. |
| Default credentials warning appears. | Default `argilla` user has default password/API key. | Startup logs; user list if authorized. | Create a strong owner/admin user, rotate/delete defaults, and replace Compose/Space sample credentials. |

## Search engine details

- Default search backend is Elasticsearch at `http://localhost:9200`.
- Set `ARGILLA_SEARCH_ENGINE=opensearch` only when the endpoint is OpenSearch.
- For TLS-backed search, prefer CA configuration through `ARGILLA_ELASTICSEARCH_CA_PATH`; disable verification only in isolated tests.
- Reindex after search backend changes, mapping/index changes, data migration, or version upgrades that affect index schemas.

## Database and persistence details

- SQLite is acceptable for local/small tests but must live under a persisted `ARGILLA_HOME_PATH` volume if data must survive restarts.
- PostgreSQL is the safer shared deployment path; use async URLs and ensure the driver is installed.
- Always run migrations against the same `ARGILLA_DATABASE_URL` that the server will use.
- Back up before migrations, reindexing, user migration, or volume changes.

## Docker and Compose log commands

```bash
# Validate without starting services.
docker compose -f scripts/docker-compose.argilla.local.yaml config

# Inspect service state after an intentional start.
docker compose --profile local-argilla -f scripts/docker-compose.argilla.local.yaml ps

# Follow logs for likely failure points.
docker compose --profile local-argilla -f scripts/docker-compose.argilla.local.yaml logs -f argilla worker elasticsearch postgres redis
```

Do not run `down -v` unless the user explicitly accepts deletion of PostgreSQL, Elasticsearch, and Argilla local volumes.
