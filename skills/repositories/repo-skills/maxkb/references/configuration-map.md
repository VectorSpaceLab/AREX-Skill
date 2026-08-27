# Configuration map

## Runtime selection
- `SERVER_NAME=web` loads the full web settings and URLs.
- `SERVER_NAME=local_model` switches to the local-model runtime.
- `main.py` sets `DJANGO_SETTINGS_MODULE=maxkb.settings` and adds `apps/` to `sys.path`.

## Config source
- `MAXKB_CONFIG_TYPE=ENV` reads `MAXKB_*` environment variables.
- Otherwise the repo uses file-based config under `/opt/maxkb/conf`.

## Core env groups
| Group | Examples | Notes |
| --- | --- | --- |
| Admin/chat prefixes | `ADMIN_PATH`, `CHAT_PATH` | Canonical route prefixes for the web app. |
| Database | `MAXKB_DB_NAME`, `MAXKB_DB_HOST`, `MAXKB_DB_PORT`, `MAXKB_DB_USER`, `MAXKB_DB_PASSWORD` | PostgreSQL-backed app state. |
| Cache/broker | `MAXKB_REDIS_HOST`, `MAXKB_REDIS_PORT`, `MAXKB_REDIS_PASSWORD`, `MAXKB_REDIS_DB`, `MAXKB_REDIS_MAX_CONNECTIONS` | Redis for cache and Celery. |
| Redis Sentinel | `MAXKB_REDIS_SENTINEL_SENTINELS`, `MAXKB_REDIS_SENTINEL_MASTER` | Optional high-availability path. |
| Local model service | `LOCAL_MODEL_HOST`, `LOCAL_MODEL_PORT`, `LOCAL_MODEL_PROTOCOL`, `LOCAL_MODEL_HOST_WORKER` | Used when serving the bundled local embeddings/reranker runtime. |
| Sandbox | `MAXKB_SANDBOX_PYTHON_BANNED_KEYWORDS`, `MAXKB_SANDBOX_PYTHON_BANNED_HOSTS`, `MAXKB_SANDBOX_PYTHON_PACKAGE_PATHS` | Restricts tool/node Python execution. |
| Serializer auth | `MAXKB_HMAC_SIGNED_SERIALIZER_SECRET_KEY` | Celery serializer/auth plumbing. |

## Canonical settings hooks
- `CONFIG.get_admin_path()` and `CONFIG.get_chat_path()` define the path prefixes.
- `CONFIG.get_db_setting()` and `CONFIG.get_cache_setting()` build Django DB/cache config.
- `apps/maxkb/settings/base/web.py` and `apps/maxkb/settings/base/model.py` split the runtime profiles.
- `apps/maxkb/urls/web.py` and `apps/maxkb/urls/model.py` mirror that split.

## Reading rule
If a task depends on a path, queue, or host, check the corresponding config hook first instead of hard-coding the value.
