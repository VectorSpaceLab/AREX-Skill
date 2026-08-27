# Argilla server CLI and configuration reference

This reference summarizes Argilla 2.8.0dev0 server commands and settings that were verified through package inspection and CLI help rendering. Commands that start services, mutate a database, or reindex search data require user approval.

## Safe help commands

These commands render help only and should not start services:

```bash
python -m argilla_server --help
python -m argilla_server start --help
python -m argilla_server database --help
python -m argilla_server database users --help
python -m argilla_server search-engine --help
python -m argilla_server worker --help
```

The bundled helper can run these help checks safely:

```bash
python scripts/check_server_cli.py --group all
```

## CLI command map

| Command | Purpose | Important options | Side effects |
| --- | --- | --- | --- |
| `python -m argilla_server` | Root Typer app. | Groups: `database`, `search-engine`; commands: `start`, `worker`. | Help only unless a subcommand is executed. |
| `python -m argilla_server start` | Start Uvicorn with `argilla_server:app`. | `--host` default `0.0.0.0`; `--port` default `6900`; `--access-log/--no-access-log`. | Long-running server; validates DB/search/Redis during app startup. |
| `python -m argilla_server database migrate` | Run Alembic migrations. | `--revision` default `head`. | Mutates database schema. Backup first in production. |
| `python -m argilla_server database revisions` | Show known DB revisions. | none. | Read-only. |
| `python -m argilla_server database users create` | Create a user and optional workspaces. | `--first-name`, `--username`, `--role owner|admin|annotator`, `--password`, `--last-name`, `--api-key`, repeated `--workspace`. | Writes users/workspaces to DB. Prompts if values are omitted. |
| `python -m argilla_server database users create_default` | Create default owner user/workspace. | `--api-key` default `argilla.apikey`; `--password` default `1234`; `--quiet/--no-quiet`. | Writes insecure defaults if not overridden; avoid in production. |
| `python -m argilla_server database users update USERNAME` | Change user role. | `--role owner|admin|annotator`. | Mutates user role in DB. |
| `python -m argilla_server database users migrate` | Migrate users from a YAML file. | Reads `ARGILLA_LOCAL_AUTH_USERS_DB_FILE`, default `.users.yml`. | Writes users/workspaces to DB. Inspect YAML and backup first. |
| `python -m argilla_server search-engine reindex` | Rebuild all dataset search indexes or one dataset. | `--dataset-id <uuid>` optional. | Deletes/recreates search indexes and reindexes records. |
| `python -m argilla_server worker` | Start RQ worker pool. | `--queues` defaults to `default, high`; `--num-workers` default `2`. | Long-running workers; requires Redis and the same service env as server. |

## Docker image startup order

The Argilla server Docker startup script performs this sequence:

1. `python -m argilla_server database migrate`
2. If both `USERNAME` and `PASSWORD` are present, create an owner user with optional `API_KEY` and `WORKSPACE`.
3. If `REINDEX_DATASETS` is `true` or `1`, run `python -m argilla_server search-engine reindex`.
4. Start Uvicorn with `python -m uvicorn $UVICORN_APP --host 0.0.0.0`.

Set `UVICORN_APP=argilla_server:app` unless intentionally extending the FastAPI app.

## Core server environment variables

All `ARGILLA_...` settings are read by server configuration unless otherwise noted.

| Variable | Meaning | Default / notes |
| --- | --- | --- |
| `ARGILLA_HOME_PATH` | Directory for local Argilla files such as SQLite DB, server ID, and local state. | Defaults to `~/.argilla`; created automatically. Mount/persist it in Docker/Spaces/K8s. |
| `ARGILLA_BASE_URL` | URL path prefix when served behind a proxy. | Defaults to `/`; normalized with leading/trailing slash. Example `/argilla`. |
| `ARGILLA_CORS_ORIGINS` | Allowed CORS origins. | Default `[*]`; for multiple origins, prefer JSON-style list syntax accepted by pydantic settings. |
| `ARGILLA_DOCS_ENABLED` | Advertised toggle for OpenAPI docs. | Default `true`; the 2.8.0dev0 settings model includes it, but if docs hardening is critical, confirm the deployed image honors the toggle because docs routes are mounted by the API app. |
| `ARGILLA_ENABLE_SHARE_YOUR_PROGRESS` | Enables share-progress UI feature. | Default `false`; feature may generate external image-link URLs if enabled. |
| `HF_HUB_DISABLE_TELEMETRY` | Disable Hugging Face Hub telemetry used by Argilla. | Set `1` to disable. |
| `HF_HUB_OFFLINE` | Disable telemetry and Hub network behavior in offline contexts. | Set `1` to disable telemetry and prefer offline behavior. |
| `ARGILLA_ENABLE_TELEMETRY` | Deprecated telemetry toggle. | `0` sets `HF_HUB_DISABLE_TELEMETRY=1`; prefer HF variables. |

## Authentication and users

| Variable | Meaning | Notes |
| --- | --- | --- |
| `USERNAME` | Docker/Space bootstrap owner username. | If paired with `PASSWORD`, startup creates an owner user. |
| `PASSWORD` | Docker/Space bootstrap owner password. | Use at least 8 characters and rotate for shared deployments. |
| `API_KEY` | Bootstrap owner Argilla API key. | If unset during CLI user creation, a secure random key can be generated. `deploy_on_spaces` requires at least 8 chars. |
| `WORKSPACE` | Bootstrap workspace name. | Startup creates/adds workspace when creating the owner user. |
| `ARGILLA_AUTH_SECRET_KEY` | Secret key for signing session/API token data. | Default is random per process; set a stable shared value for multiple workers/instances or restarts. |
| `ARGILLA_AUTH_ALGORITHM` | JWT/signing algorithm. | Default `HS256`. |
| `ARGILLA_AUTH_TOKEN_EXPIRATION` | Session token lifetime in seconds. | Default `86400` (1 day). |
| `ARGILLA_AUTH_OAUTH_CFG` | OAuth config file path. | Code default is `.oauth.yaml`; set explicitly if using `.oauth.yml` or a mounted path. |

## Database configuration

| Variable | Meaning | Default / notes |
| --- | --- | --- |
| `ARGILLA_DATABASE_URL` | SQLAlchemy async database URL. | Defaults to SQLite under `ARGILLA_HOME_PATH`: `sqlite+aiosqlite:///<home>/argilla.db?check_same_thread=False`. |
| `ARGILLA_DATABASE_SQLITE_TIMEOUT` | SQLite lock wait timeout in seconds. | Default `5` in 2.8.0dev0 source. Increase only for local/small deployments. |
| `ARGILLA_DATABASE_POSTGRESQL_POOL_SIZE` | PostgreSQL pool size. | Default `15`. |
| `ARGILLA_DATABASE_POSTGRESQL_MAX_OVERFLOW` | Extra PostgreSQL connections over pool size. | Default `10`. |

URL normalization behavior: `sqlite:///...` is converted to `sqlite+aiosqlite:///...`, and `postgresql://...` or `postgresql+psycopg2://...` is converted to `postgresql+asyncpg://...` with a warning. If installing from pip and using PostgreSQL, ensure async PostgreSQL support is installed.

## Search engine configuration

| Variable | Meaning | Default / notes |
| --- | --- | --- |
| `ARGILLA_ELASTICSEARCH` | Search engine endpoint URL. | Default `http://localhost:9200`; used for Elasticsearch or OpenSearch endpoint naming. |
| `ARGILLA_SEARCH_ENGINE` | Backend implementation. | `elasticsearch` default; valid values include `elasticsearch` and `opensearch`. |
| `ARGILLA_ELASTICSEARCH_SSL_VERIFY` | TLS certificate verification. | Default `true`; set `false` only for trusted/private test endpoints. |
| `ARGILLA_ELASTICSEARCH_CA_PATH` | Path to CA certificate file. | Use for custom CA/TLS search clusters. |
| `ARGILLA_ES_RECORDS_INDEX_SHARDS` | Shards for dataset record indexes. | Default `1`. |
| `ARGILLA_ES_RECORDS_INDEX_REPLICAS` | Replicas for dataset record indexes. | Default `0`. |
| `ARGILLA_ES_MAPPING_TOTAL_FIELDS_LIMIT` | Mapping total fields limit. | Default `2000` from server settings. |
| `REINDEX_DATASETS` | Docker image startup reindex flag. | If `true` or `1`, startup runs full search-engine reindex. |

Argilla expects Elasticsearch >= 8.5.0 or OpenSearch >= 2.4.0 for the selected backend. For OpenSearch vector search, filtering with k-NN uses a `post_filter` workaround, so combined filter/vector results may differ from Elasticsearch.

## Redis and worker configuration

| Variable | Meaning | Default / notes |
| --- | --- | --- |
| `ARGILLA_REDIS_URL` | Redis URL for background jobs. | Default `redis://localhost:6379/0`; server and workers must use the same URL. |
| `ARGILLA_REDIS_USE_CLUSTER` | Use Redis Cluster connection behavior. | Default `false`. |
| `BACKGROUND_NUM_WORKERS` | Common Docker/K8s convenience variable for worker count. | Feed into `python -m argilla_server worker --num-workers ${BACKGROUND_NUM_WORKERS}`. |

The server pings Redis on startup. Worker processes are required for background jobs and should share DB/search/Redis/home settings with the server.

## Dataset and schema limits

| Variable | Meaning | Default / notes |
| --- | --- | --- |
| `ARGILLA_LABEL_SELECTION_OPTIONS_MAX_ITEMS` | Maximum label/multilabel question options. | Default `500`. |
| `ARGILLA_SPAN_OPTIONS_MAX_ITEMS` | Maximum span question options. | Default `500`. |
| `ARGILLA_MIN_MESSAGE_LENGTH` / `ARGILLA_MAX_MESSAGE_LENGTH` | Chat message content length validation. | Defaults `1` / `20000`. |
| `ARGILLA_MIN_ROLE_LENGTH` / `ARGILLA_MAX_ROLE_LENGTH` | Chat role string length validation. | Defaults `1` / `20`. |

## OAuth2 and SSO configuration

Argilla reads OAuth settings from the file configured by `ARGILLA_AUTH_OAUTH_CFG`. The 2.8.0dev0 code default is `.oauth.yaml`; set the env var explicitly when the mounted file uses another name.

Minimal shape:

```yaml
providers:
  - name: huggingface
    client_id: "<client-id>"
    client_secret: "<client-secret>"
    scope: "openid profile"

  - name: github
    client_id: "<client-id>"
    client_secret: "<client-secret>"

  - name: google-oauth2
    client_id: "<client-id>"
    client_secret: "<client-secret>"
    scope: "openid email profile"

allowed_workspaces:
  - name: argilla

allow_http_redirect: false
```

Provider notes:

- Built-in provider names include `huggingface`, `github`, `google-oauth2`, and `keycloak`.
- The redirect URI registered with the OAuth provider should be the externally visible server URL plus `/oauth/<provider-name>/callback`, for example `https://argilla.example.org/oauth/huggingface/callback`.
- Provider fields can be supplied in YAML or, for provider names that form valid environment variables, through 2.8.0dev0 overrides without an `ARGILLA_` prefix: `OAUTH2_<PROVIDER_NAME>_CLIENT_ID`, `OAUTH2_<PROVIDER_NAME>_CLIENT_SECRET`, and `OAUTH2_<PROVIDER_NAME>_SCOPE`. Examples: `OAUTH2_HUGGINGFACE_CLIENT_ID` and `OAUTH2_GITHUB_CLIENT_SECRET`. For hyphenated provider names such as `google-oauth2`, prefer YAML (or provider-specific Social Auth settings) because shell environment variables cannot contain hyphens.
- `allowed_workspaces` controls the workspaces OAuth-authenticated users can join. Server startup creates missing allowed workspaces in 2.8.0dev0, but you should still make the list intentional.
- `allow_http_redirect: true` sets OAuthlib insecure-transport behavior for local/proxy tests. Do not use it for production; prefer HTTPS and correct forwarded headers.
- Extra providers can be registered by adding `extra_backends` with Social Auth backend class paths, then adding a matching provider entry.

Keycloak-specific notes:

```yaml
allow_http_redirect: false
providers:
  - name: keycloak
    client_id: "argilla-client"
    client_secret: "<client-secret>"
    redirect_uri: "https://argilla.example.org/oauth/keycloak/callback"
allowed_workspaces:
  - name: default
```

Set `SOCIAL_AUTH_OIDC_ENDPOINT` to the Keycloak realm endpoint, such as `https://keycloak.example.org/realms/argilla`. Keycloak realm roles named `argilla_role:<owner|admin|annotator>` and `argilla_workspace:<workspace>` are read from realm roles when available.
