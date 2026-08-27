# Backend workflows, settings, and DB utilities

This reference covers local backend development, service prerequisites, environment settings, Celery worker notes, Alembic behavior, and DB-backed export/import semantics. It intentionally does not include model training, production deployment, Next.js UI implementation, or inference server operation.

## Local development service prerequisites

### Minimal Python/service layout

A backend checkout needs these Python import roots available together:

- Backend application package containing `main:app` and `oasst_backend`.
- Shared package containing `oasst_shared` protocol schemas, API client, exceptions, and model/inference schemas.
- Data package containing `oasst_data` JSONL schemas/readers/writers/traversal helpers.

For read-only import checks, use the bundled script:

```bash
python scripts/check_backend_python.py --repo-root <repo-root>
```

For route-name inspection without starting uvicorn:

```bash
python scripts/check_backend_python.py --repo-root <repo-root> --openapi
```

### Docker backend-dev profile

For local backend service work, start the backend-dev dependency profile from the repository root:

```bash
docker compose --profile backend-dev up --build --attach-dependencies
```

The backend-dev profile provides PostgreSQL on host port `5432`, Redis on host port `6379`, RedisInsight on host port `8001`, and Adminer on host port `8089` when those profile services are enabled by compose.

On Apple Silicon/M-series machines, use the DB platform override when the PostgreSQL image requires x86_64 compatibility:

```bash
DB_PLATFORM=linux/x86_64 docker compose --profile backend-dev up --build --attach-dependencies
```

### Local Python install sequence

From a Python 3.10 environment intended for backend development:

```bash
python -m pip install -r <repo-root>/backend/requirements.txt
python -m pip install -e <repo-root>/oasst-shared
python -m pip install -e <repo-root>/oasst-data
```

Use a clean environment if dependency metadata is inconsistent; Celery/Redis/FastAPI stacks are sensitive to older package metadata left in shared environments.

### `.env` essentials

Create a backend `.env` for local service runs. The settings model reads `.env`, is case-insensitive, and uses nested delimiter `__` for nested settings.

Core variables:

```dotenv
DATABASE_URI="postgresql://postgres:postgres@localhost:5432/postgres"
REDIS_HOST=localhost
REDIS_PORT=6379
HUGGING_FACE_API_KEY=
BACKEND_CORS_ORIGINS_CSV=http://localhost:3000,http://localhost:8080
DEBUG_SKIP_EMBEDDING_COMPUTATION=True
DEBUG_SKIP_TOXICITY_CALCULATION=True
```

For local frontend/task testing, common debug toggles are:

```bash
export DEBUG_USE_SEED_DATA=True
export DEBUG_ALLOW_SELF_LABELING=True
export DEBUG_ALLOW_SELF_RANKING=True
export DEBUG_ALLOW_DUPLICATE_TASKS=True
```

Keep embedding/toxicity skips set to `True` unless the user explicitly wants Hugging Face API calls and has configured credentials.

### Run uvicorn locally

From the backend application working directory with shared/data packages importable:

```bash
export DEBUG_SKIP_EMBEDDING_COMPUTATION=True
export DEBUG_SKIP_TOXICITY_CALCULATION=True
export DEBUG_USE_SEED_DATA=True
export DEBUG_ALLOW_SELF_LABELING=True
export DEBUG_ALLOW_SELF_RANKING=True
export DEBUG_ALLOW_DUPLICATE_TASKS=True
uvicorn main:app --reload --port 8080 --host 0.0.0.0
```

The server should expose API docs at `http://localhost:8080/docs` and OpenAPI JSON at `http://localhost:8080/api/v1/openapi.json`.

### Mock backend from OpenAPI

A mock backend can be built by generating OpenAPI JSON from the app and serving it with an OpenAPI mock server. This is useful for frontend contract tests but does not validate database behavior.

Safe sequence:

```bash
python -m main --print-openapi-schema > openapi.json
# Serve openapi.json with a local OpenAPI mock tool if one is already installed.
```

Do not treat mock-server success as proof that task lifecycle, DB queries, Redis rate limits, or Celery work are healthy.

### Celery worker notes

Celery workers are used for Hugging Face toxicity and feature extraction tasks, and Celery Beat schedules periodic tasks such as user stats/streak updates.

Run only when Redis is available and the user explicitly wants worker behavior:

```bash
celery -A oasst_backend.celery_worker worker -l INFO -B
```

For API-only local development, keep:

```bash
DEBUG_SKIP_TOXICITY_CALCULATION=True
DEBUG_SKIP_EMBEDDING_COMPUTATION=True
```

Set both to `False` only when API keys, network access, and worker runtime are intentionally in scope.

## Settings model essentials

`Settings` is a Pydantic `BaseSettings` model. Defaults are suitable for local backend-dev Docker services unless overridden.

### Database URI assembly

If `DATABASE_URI` is supplied, it is used directly.

If `DATABASE_URI` is omitted, it is assembled as:

```text
postgresql://<POSTGRES_USER>:<POSTGRES_PASSWORD>@<POSTGRES_HOST>:<POSTGRES_PORT>/<POSTGRES_DB>
```

Default components:

| Field | Default |
| --- | --- |
| `POSTGRES_HOST` | `localhost` |
| `POSTGRES_PORT` | `5432` |
| `POSTGRES_USER` | `postgres` |
| `POSTGRES_PASSWORD` | `postgres` |
| `POSTGRES_DB` | `postgres` |

Native settings tests assert both direct connection-string usage and assembled URI behavior.

### Environment nesting

- `env_file`: `.env`
- `case_sensitive`: `False`
- `env_nested_delimiter`: `__`

Nested TreeManager settings can be overridden with names such as:

```bash
export TREE_MANAGER__MAX_TREE_DEPTH=4
export TREE_MANAGER__MAX_CHILDREN_COUNT=2
```

### High-impact backend flags

| Field | Default | Why it matters |
| --- | --- | --- |
| `API_V1_STR` | `/api/v1` | Prefix for all backend REST routes and OpenAPI JSON. |
| `OFFICIAL_WEB_API_KEY` | `1234` | Used to create/validate the official web API client at startup when set. |
| `ROOT_TOKENS` | `["1234"]` | Bearer tokens authorized to create API clients through admin route. |
| `RATE_LIMIT` | `True` | Enables Redis-backed FastAPI rate limits. Disable for isolated local debugging if Redis is unavailable. |
| `MESSAGE_SIZE_LIMIT` | `2000` | Max characters accepted by `TextReplyToMessage`. |
| `REDIS_HOST`, `REDIS_PORT` | `localhost`, `6379` | Redis target for limiter and Celery broker/backend in local setups. |
| `DEBUG_USE_SEED_DATA` | `False` | Inserts seed tasks/messages at startup; requires official web API key. |
| `DEBUG_ALLOW_SELF_LABELING` | `False` | Allows users to label own messages in local testing. |
| `DEBUG_ALLOW_SELF_RANKING` | `False` | Allows users to rank own messages in local testing. |
| `DEBUG_ALLOW_DUPLICATE_TASKS` | `False` | Allows repeated user tasks/replies in local testing. |
| `DEBUG_SKIP_EMBEDDING_COMPUTATION` | `False` | Skips feature extraction Celery call when `True`. |
| `DEBUG_SKIP_TOXICITY_CALCULATION` | `False` | Skips toxicity Celery call when `True`. |
| `DEBUG_IGNORE_TOS_ACCEPTANCE` | `True` | Ignores ToS acceptance in user checks. |
| `UPDATE_ALEMBIC` | `True` | Attempts Alembic upgrade on startup. |
| `ENABLE_PROM_METRICS` | `True` | Exposes Prometheus metrics at `/metrics`. |
| `TASK_VALIDITY_MINUTES` | `2880` | Personal tasks expire after two days. |

### TreeManagerConfiguration fields to know

TreeManager configuration controls task sampling, tree growth, review/ranking thresholds, moderation, and backlog activation.

| Field group | Important fields |
| --- | --- |
| Tree size/shape | `max_active_trees`, `max_tree_depth`, `max_children_count`, `goal_tree_size`, `random_goal_tree_size`, `min_goal_tree_size`, `lonely_children_count`, `p_lonely_child_extension` |
| Review/ranking thresholds | `num_reviews_initial_prompt`, `num_reviews_reply`, `acceptance_threshold_initial_prompt`, `acceptance_threshold_reply`, `num_required_rankings`, `rank_prompter_replies` |
| Label selection | `labels_initial_prompt`, `labels_assistant_reply`, `labels_prompter_reply`, `mandatory_labels_initial_prompt`, `mandatory_labels_assistant_reply`, `mandatory_labels_prompter_reply`, full-labeling probabilities |
| Auto moderation | `auto_mod_enabled`, `auto_mod_max_skip_reply`, `auto_mod_red_flags` |
| Backlog/activation | `p_activate_backlog_tree`, `min_active_rankings_per_lang`, `max_prompt_lottery_waiting`, `init_prompt_disabled_langs` |
| User task throttling | `recent_tasks_span_sec`, `max_pending_tasks_per_user` |

`init_prompt_disabled_langs_list` is a derived comma-split list from `init_prompt_disabled_langs`.

## Alembic behavior

When `UPDATE_ALEMBIC=True`, app startup attempts to upgrade the database schema to head using the configured `DATABASE_URI`. If startup logs show migration failures, fix DB connectivity/schema before debugging route handlers.

When creating migrations, the normal project workflow is to autogenerate a revision from model changes, review the generated script, and apply it through Alembic. Do not invent migration SQL from this sub-skill alone.

## DB-backed export behavior

The backend export utility connects to the same database engine/settings as the REST backend. It is a read operation against the DB but writes JSONL output.

Important filters and effects:

| Option concept | Behavior |
| --- | --- |
| `lang` | Select trees by prompt language or messages by message language. |
| `state` | Default state is `ready_for_export`; `all` disables state filter. |
| `include_deleted` / deleted-only | Controls deleted-message filtering. |
| `include_spam` / spam-only | Controls `review_result`; spam means failed review (`False`). |
| `include_synthetic` / synthetic-only | Controls synthetic-message filtering. |
| `user` | Exports messages involving one user; incompatible with state filter and produces flat messages rather than complete trees. |
| `prompts_only` | Exports root prompt messages or prompts within trees. |
| `export_labels` | Adds average label values and counts. |
| `export_events` | Adds emoji/rating/ranking event details. |
| `limit` | Limits selected trees/messages. |
| `anonymizer_seed` | Enables deterministic anonymization when supplied. |
| output suffix `.gz` | Enables gzip compression. |

Output shape:

- Complete, normal tree exports are written as `ExportMessageTree` JSONL objects.
- Filtered outputs that cannot preserve complete trees are written as flat `ExportMessageNode` message objects.
- Corrupted trees are skipped with warnings rather than crashing the entire export.

Safe follow-up: use `scripts/oasst_jsonl_tool.py inspect` and `tree-to-messages` on exported files before downstream data transformations.

## DB-backed import behavior

Import is database-mutating unless dry-run rollback is used. It reads JSONL line by line and supports tree or message objects.

Behavior distilled:

- Creates or reuses a well-known import API client.
- Looks up a system import user.
- For tree objects, validates `message_tree_id == prompt.message_id` and inserts messages recursively.
- Imported tree states are limited to backlog ranking or active ranking; `num_activate` controls how many imported trees enter active ranking.
- Existing message trees/messages are skipped, not duplicated.
- `model_name` argument supplies a default model name when missing on imported messages.
- `max_count` stops after a bounded number of imported trees/messages.
- `dry_run=True` uses transaction rollback and logs that no DB commit should remain.

Before any real import, require the user to confirm:

1. Target database identity and connection string.
2. Backup/rollback plan.
3. Whether the input file has been inspected and whether it contains trees or messages.
4. Desired `origin`, `model_name`, `num_activate`, and `max_count`.
5. Whether dry-run should be performed first.

This generated sub-skill intentionally does not bundle a DB-mutating import wrapper.

## Source-script adaptation decisions for this sub-skill

- Local backend server shell behavior was distilled into the uvicorn/debug environment commands above rather than copied directly, because the safe reusable form needs explicit arguments and should not assume the caller's current directory.
- Mock-server behavior is reference-only: generating and serving OpenAPI may require Docker or external mock tooling and is not a backend correctness check.
- Worker shell behavior is distilled into the Celery command above; running it has service side effects and should be user-confirmed.
- DB export/import behavior is documented but not bundled as executable scripts because import can mutate a database and export depends on a live DB connection.
- OA JSONL examples were adapted into the bundled safe [`../scripts/oasst_jsonl_tool.py`](../scripts/oasst_jsonl_tool.py).
