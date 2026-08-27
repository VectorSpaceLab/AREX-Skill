# Backend troubleshooting

Start with the symptom, check the likely cause, then run only the smallest safe validation command. Avoid destructive DB operations unless the user explicitly authorizes them.

## Import and Python environment failures

| Symptom | Likely cause | Recovery/check |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'oasst_backend'` | Backend application import root is not on `PYTHONPATH`, or backend requirements are not installed. | Use `python scripts/check_backend_python.py --repo-root <repo-root>` from this sub-skill. Ensure the backend application package is importable and install backend requirements in a clean Python 3.10 environment. |
| `ModuleNotFoundError: No module named 'oasst_shared'` | Shared package not installed/editable or not on `PYTHONPATH`. | Install the shared package in the same environment used for backend work, or pass the correct repo root to the bundled check script. |
| `ModuleNotFoundError: No module named 'oasst_data'` | Data package not installed/editable. | Install the data package for Python helpers. For basic file inspection/filtering, `scripts/oasst_jsonl_tool.py` can still operate with the standard-library fallback. |
| Import errors involving FastAPI, SQLModel, Redis, Celery, Pydantic, or Loguru | Backend requirements missing or incompatible. | Use a fresh environment and reinstall the backend requirement set plus editable shared/data packages. |
| Pip complains about old Celery metadata or invalid requirement metadata | Reused environment contains stale package metadata or a pip version/metadata compatibility issue. | Prefer a clean environment. If staying in the same environment, upgrade packaging tools deliberately, then reinstall backend requirements; do not mutate a user-managed environment without permission. |

## PostgreSQL, Redis, and service startup

| Symptom | Likely cause | Recovery/check |
| --- | --- | --- |
| Backend startup cannot connect to PostgreSQL | DB container down, wrong host/port, wrong `DATABASE_URI`, or server not ready. | Start backend-dev Docker profile, verify host port `5432`, and confirm `DATABASE_URI` or `POSTGRES_*` fields assemble to the intended DB. |
| Startup logs show Alembic upgrade failed | DB is unreachable, connection string is wrong, or migration state is broken. | Fix DB connectivity first. If DB is correct, inspect Alembic revision state before changing models. |
| Rate-limit initialization logs Redis connection failure | `RATE_LIMIT=True` but Redis is unavailable or `REDIS_HOST`/`REDIS_PORT` are wrong. | Start Redis, correct settings, or temporarily set `RATE_LIMIT=False` for isolated local route debugging. |
| Requests return too-many-requests errors | Redis-backed limiter is active and user/API task limit was exceeded. | Wait for limiter window, use a different test user/API key, or disable rate limit only for local debugging. |
| Celery worker cannot connect | Redis broker/backend is unavailable or worker dependencies missing. | Start Redis and install worker requirements before running `celery -A oasst_backend.celery_worker worker -l INFO -B`. Keep embedding/toxicity skips true when worker/API calls are out of scope. |
| Uvicorn starts but docs route is missing | Wrong module/app imported or wrong port/prefix. | Confirm command uses `main:app`, port `8080`, and API prefix `/api/v1`. Use the bundled check script with `--openapi` without starting a server. |

## Settings and `.env` mistakes

| Symptom | Likely cause | Recovery/check |
| --- | --- | --- |
| `DATABASE_URI` ignored or surprising URI assembled | `DATABASE_URI` omitted, malformed, or overridden by environment. | If explicit URI is desired, set `DATABASE_URI` directly. Otherwise check `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`. |
| Nested TreeManager values do not change | Wrong nested environment key syntax. | Use `TREE_MANAGER__FIELD_NAME=value`, e.g. `TREE_MANAGER__MAX_TREE_DEPTH=4`. Settings are case-insensitive but the delimiter is double underscore. |
| CORS origins fail validation | JSON/list syntax or CSV setting mismatch. | Prefer `BACKEND_CORS_ORIGINS_CSV=http://localhost:3000,http://localhost:8080` for simple local work. |
| Seed data startup fails | `DEBUG_USE_SEED_DATA=True` without an official web API key or DB state is not ready. | Set `OFFICIAL_WEB_API_KEY` and ensure DB migrations completed, or disable seed data. |
| Hugging Face calls unexpectedly happen | Debug skip flags are false. | Set `DEBUG_SKIP_EMBEDDING_COMPUTATION=True` and `DEBUG_SKIP_TOXICITY_CALCULATION=True` unless worker/API behavior is in scope. |

## API auth failures

| Symptom | Likely cause | Recovery/check |
| --- | --- | --- |
| `API_CLIENT_NOT_AUTHORIZED` or HTTP 403 on normal API route | Missing/invalid API key or disabled API client. | Send `X-API-Key` header or `api_key` query parameter with an enabled API client key. |
| Trusted/admin endpoint returns forbidden | API client exists but is not trusted. | Create/use a trusted API client only in a confirmed local/admin context. |
| Creating API client fails with `ROOT_TOKEN_NOT_AUTHORIZED` | Missing/invalid bearer token. | Use `Authorization: Bearer <root-token>` where token is included in `Settings.ROOT_TOKENS`. Do not confuse root token with `X-API-Key`. |
| Frontend-user routes behave as anonymous | Missing/malformed frontend user identity. | Use `x-oasst-user: auth_method:username` or include `user` in task request/interactions as required. |
| `/auth/check` fails | NextAuth cookie missing, wrong cookie name, or auth secret/salt/info mismatch. | Confirm the configured auth cookie name and encryption settings match the web frontend environment. |

## Task lifecycle errors

| Symptom/error code | Likely cause | Recovery/check |
| --- | --- | --- |
| `TASK_NOT_FOUND` | Wrong task UUID or frontend message id, or API client mismatch. | Track both backend task id and frontend message id; ACK uses task UUID, interaction uses frontend message id. |
| `TASK_EXPIRED` | Task older than `TASK_VALIDITY_MINUTES` (default two days). | Fetch a fresh task. Do not submit stale interactions. |
| `TASK_NOT_ACK` | Interaction submitted before ACK. | Call `ack_task(task.id, frontend_task_message_id)` before `post_interaction`. |
| `TASK_ALREADY_UPDATED` | ACK/NACK/update attempted after task already acked/done, or ACK repeated with a different frontend id. | Repeated ACK is safe only with the exact same frontend message id. Otherwise fetch a new task. |
| `TASK_ALREADY_DONE` | Interaction/close submitted for a completed task. | Do not retry completed interactions blindly; fetch a fresh task. |
| `TASK_NOT_ASSIGNED_TO_USER` | Interaction user does not match personal task assignment. | Use the same protocol `User` identity throughout request, ACK, and interaction. |
| `TASK_NOT_COLLECTIVE` | `/tasks/close` used on a personal task. | Close only collective tasks. For personal tasks, submit the appropriate interaction. |
| `TASK_TOO_MANY_PENDING` | User has too many uncompleted recent tasks. | Complete/skip pending tasks, wait for recent span, use a different test user, or adjust TreeManager pending-task settings for local debugging. |
| `TASK_MESSAGE_TEXT_EMPTY` | Text is empty or whitespace. | Submit non-empty trimmed text. |
| `TASK_MESSAGE_TOO_LONG` | Text length exceeds `MESSAGE_SIZE_LIMIT`, default 2000. | Shorten text or intentionally adjust the setting in a local test environment. |
| `TASK_MESSAGE_DUPLICATED` | Recent duplicate reply detected. | Change test text or enable duplicate debug flag only in local testing. |
| `TASK_MESSAGE_DUPLICATE_REPLY` | Same user replied twice to the same parent. | Use a different user/test path or enable duplicate-task debug flag only in local testing. |
| `TREE_IN_ABORTED_STATE` | Message tree no longer accepts replies. | Fetch a new task from an active tree. |
| `TEXT_LABELS_MANDATORY_LABEL_MISSING` | Label task omitted a mandatory label such as spam. | Include every mandatory label returned by the task/valid-label endpoint. |

## Cursor and pagination issues

| Symptom | Likely cause | Recovery/check |
| --- | --- | --- |
| `INVALID_CURSOR_VALUE` | Cursor is not ISO datetime and not `uuid$iso_datetime`. | Use the exact `prev` or `next` returned by the API. Do not URL-decode away the `$` separator incorrectly. |
| Unsupported user cursor sort key | `sort_key` is not `username` or `display_name`. | Use one of the supported sort keys. |
| Page order appears reversed | `before`, `after`, and `desc` interact to fetch reverse slices then normalize output. | Preserve the returned `prev`/`next` tokens and `order` instead of constructing cursors manually. |

## OA JSONL data failures

| Symptom | Likely cause | Recovery/check |
| --- | --- | --- |
| JSON decode error at line N | Invalid JSONL line or compressed file opened as plain text. | Confirm extension and run `python scripts/oasst_jsonl_tool.py inspect <file>`. |
| Unknown JSONL object | No top-level `message_id`, `message_tree_id`, or `thread_id`. | Fix input generation or transform to one of the supported OA object shapes. |
| Tree flattening fails | Tree object has `message_tree_id` but no `prompt`. | Inspect the file; it may contain partial metadata rather than full tree exports. |
| Flat message split fails due to missing `message_tree_id` | Messages were not flattened from full trees or tree context was dropped. | Re-run tree flattening so every message carries `message_tree_id`, or pass `--fallback-id` only if per-message grouping is acceptable. |
| Filter output unexpectedly empty | Defaults exclude deleted, failed-review/spam, and synthetic messages. | Add `--include-deleted`, `--include-spam`, or `--include-synthetic` when those should be kept. |
| Missing `message_id` | Invalid flat message object. | Every message operation requires `message_id`; repair source data before filtering/splitting. |
| Missing `message_tree_id` in tree object | Invalid full tree object. | Full-tree operations require top-level `message_tree_id`; repair source data before import or filtering. |

## DB export/import safety checklist

Before a DB export:

1. Confirm target `DATABASE_URI` and whether output may contain private data.
2. Decide filters for language, state, deleted/spam/synthetic, labels, events, and anonymization seed.
3. Inspect the resulting JSONL with the bundled tool before downstream use.

Before a DB import:

1. Require explicit user approval; import mutates the database unless dry-run rollback is selected.
2. Confirm backup/rollback plan and target DB identity.
3. Inspect input JSONL and verify whether it contains trees or flat messages.
4. Run a dry run first when possible.
5. Confirm `origin`, `model_name`, active tree count, and maximum import count.
