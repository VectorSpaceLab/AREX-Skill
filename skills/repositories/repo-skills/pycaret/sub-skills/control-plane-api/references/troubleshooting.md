# Control Plane API troubleshooting

Start with safe checks:

```bash
pycaret-server version
pycaret-server doctor
python scripts/server_smoke.py --json
python scripts/run_lifecycle_smoke.py --plan setup --timeout-s 60 --json
```

Then inspect the exact failing HTTP response body. The backend usually returns a
specific `detail` string for validation failures.

## Bootstrap and auth

| Symptom | Likely cause | Fix |
|---|---|---|
| `409 instance already bootstrapped` from `/setup/bootstrap` | A user already exists. | Login through `/auth/login`, or intentionally use a new SQLite DB/data dir for a fresh instance. Do not keep retrying bootstrap. |
| `401 missing Authorization or X-PyCaret-Key header` | Protected route called without auth. | Add `Authorization: Bearer <access_token>` or `X-PyCaret-Key: <pck_...>`. |
| `401 invalid access token` or `access token expired` | Expired/malformed JWT or wrong token type. | Use `/auth/refresh` with the refresh token, or login again. Access tokens, not refresh tokens, go in the bearer header. |
| `401 invalid API key`, `API key revoked`, or `API key expired` | Programmatic key hash did not match an active row. | Create a new key with `POST /auth/api-keys`; plaintext is returned once. |
| `403 not a member of this workspace` | User lacks membership. | Add a `WorkspaceMember`, use the correct workspace id, or authenticate as a superuser. |
| `403 workspace admin required` | Route needs admin-equivalent role. | Use `owner`, `admin`, `project_admin`, or superuser. |
| `/api/v1/setup/me` returns `501` | Stub kept for first-run flow. | Use `/api/v1/auth/me`. |

## SQLite, Alembic, and settings cache

| Symptom | Likely cause | Fix |
|---|---|---|
| `no such table: users` or missing app tables | DB was not migrated/created. | For local SQLite, start the app or run `pycaret-server migrate --url sqlite:///...`. For tests, create metadata or let lifespan auto-migrate. For Postgres/MySQL, run migrations explicitly before serve. |
| `Database is empty and dev_auto_migrate=False` | Non-SQLite production DB started without migrations. | Run `pycaret-server migrate --url <database-url>` or Alembic upgrade before starting the API. |
| `--reset-dev refuses to touch a non-SQLite URL` | Safety guard. | Drop/recreate the production DB manually after backup; `--reset-dev` is SQLite-only. |
| Env var changes ignored in a long-lived Python process | `get_settings()` and some singletons are cached. | Clear `pycaret_server.config.get_settings.cache_clear()` and reset storage/crypto/router/orchestrator/registry/scheduler singletons, or restart the process. |
| TestClient uses the wrong DB | `pycaret_server.db.session.engine` was created before env changed. | Rebind `engine` and `session_factory` after setting temp env vars; see `cli-and-config.md`. |

## Secret key and encrypted secrets

| Symptom | Likely cause | Fix |
|---|---|---|
| Warning: `PYCARET_SECRETS_KEY is not set. Using an EPHEMERAL key` | Dev convenience key generated per process. | Set a Fernet key before storing real LLM keys, connection passwords, webhooks, or Git PATs. |
| `Could not decrypt stored secret` | Fernet key changed or server restarted after using an ephemeral key. | Restore the old key if available, or re-enter every affected secret via API. |
| `PYCARET_SECRETS_KEY is set but not a valid Fernet key` | Key is not base64-url-safe 32 bytes. | Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. |
| LLM settings response lacks `api_key` | Intentional. | Use `has_api_key` to tell whether a key is stored; plaintext is never returned. |

## Data sources and catalog

| Symptom | Likely cause | Fix |
|---|---|---|
| `kind must be one of ['postgres', 's3']; use /upload for csv_upload` | Attempted to register CSV through connector endpoint. | Use multipart `/workspaces/{workspace_id}/data-sources/upload`. |
| `data source kind 's3' not yet supported for runs` | Run dispatch currently trains only from uploaded CSV DataSources, sklearn datasets, or inline data. | Materialize to `csv_upload` or use sklearn/inline data for the Run. Profile/version S3/Postgres through catalog endpoints only. |
| `uploaded file no longer exists on disk` (`410`) | CSV file path in DataSource config is missing. | Re-upload the CSV or restore artifacts from backup. |
| `data source belongs to a different workspace` | Experiment and DataSource workspace mismatch. | Use a DataSource in the same workspace as the experiment's project. |
| `could not parse CSV` or `could not read CSV` | Invalid CSV, encoding issue, or path missing. | Validate with pandas locally, then re-upload. |
| `no datasource driver registered for kind=...` | Driver kind not registered in the installed backend. | Use `GET /datasource-kinds` and select a supported kind or add/register a driver. |
| Postgres connection errors | Bad host/user/database/password or missing driver dependency. | Create/update Secret, test `/connections/{id}/test`, and ensure the server environment has the Postgres extra. |

## Storage and artifacts

| Symptom | Likely cause | Fix |
|---|---|---|
| `unknown PYCARET_STORAGE_BACKEND` | Env var is not `local`, `s3`, or `minio`. | Correct `PYCARET_STORAGE_BACKEND` and reset/restart. |
| `S3ObjectStore requires a bucket name` | S3/MinIO backend selected without bucket. | Set `PYCARET_STORAGE_BUCKET`. |
| `boto3 is not installed` | S3/MinIO selected without optional SDK. | Install `pycaret-server[s3]` or add `boto3` to the server environment. |
| `pipeline artifact not found` | Artifact URI points to missing local file/object. | Restore artifact storage, check bucket/key, or retrain/promote a new Trial. |
| Trial download returns `410 GONE` | Local file referenced by `stored_path` is gone. | Recreate from backup or rerun. |
| Local object-store traversal error | Key attempted to escape artifact root. | Treat as invalid/unsafe key; do not bypass the guard. |

## Run and Trial failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `invalid plan` | Plan not in `setup|create|compare|search`. | Correct `RunCreate.plan`. |
| `plan='create' requires model_id` | Create run missing `model_id`. | Include a valid PyCaret model id such as `lr` for classification. |
| `must supply sklearn_dataset, data_inline, or data_source_id` | No data input. | Provide one input source. |
| `unknown sklearn dataset` | Built-in name not in the server list. | Use `iris`, `wine`, `breast_cancer`, or `diabetes`, or provide data another way. |
| Run remains `queued` with in-process backend | Executor is stuck or app process is shutting down. | Check server logs; restart app; rerun with `scripts/run_lifecycle_smoke.py --plan setup`. |
| Run remains `queued` with Redis backend | Worker not running, wrong queues, Redis unavailable, or GPU queue has no GPU worker. | Check `pycaret-server doctor`, `/admin/queues`, `/admin/system`, worker `--queues`, and Redis URL. |
| Run status `failed` | Engine/data/config error persisted in `Run.error`; Trial errors may be more specific. | `GET /runs/{run_id}`, `GET /runs/{run_id}/events?tail=true`, and `GET /runs/{run_id}/trials`; debug failed runs with `/llm/debug-run` when LLM is configured. |
| Follow-on tune/ensemble fails | Source Trial missing artifact or source Run snapshot data cannot be reloaded. | Confirm Run is `succeeded`, Trial has `has_artifact=true`, and original DataSource still exists. |
| Blend/stack says source trials not found | Source ids do not match the Run grouping expected by the endpoint. | Use ids returned by `GET /runs/{run_id}/trials`; ensure at least two source Trials from the same succeeded Run. |
| CV/cohort endpoint says target missing | Run snapshot lacks a usable target column. | Use a supervised task with `target`, or call only for supported classification/regression Trials. |

## WebSockets and event streams

| Symptom | Likely cause | Fix |
|---|---|---|
| WebSocket closes `4401` | Missing/invalid `?token=` or inactive user. | Append a current access token in the query string. |
| WebSocket closes `4403` | Token user lacks workspace access to the Run. | Use a token for a workspace member/superuser. |
| No live events but polling shows events | Proxy/transport issue or run already terminal. | The WS should replay stored events then send `run.closed` for terminal Runs. Check proxy supports WebSocket upgrades and use `GET /runs/{id}/events` as fallback. |
| Event list is huge | Long runs can emit many events. | Use `tail=true&limit=50` or `after_id`. |

## Promotion, deployment, and prediction

| Symptom | Likely cause | Fix |
|---|---|---|
| `only succeeded runs can be promoted` | Run still queued/running/failed. | Wait for success or promote a succeeded Trial. |
| `trial status is ...; only succeeded trials can be promoted` | Trial not terminal-success. | Promote a succeeded Trial. |
| `trial has no stored pipeline artifact` | Old/failed Trial lacks pickle. | Rerun create/compare and verify `has_artifact=true`. |
| `endpoint_slug ... already in use` | Slug is globally unique. | Choose another slug. |
| `endpoint_slug must match ...` | Invalid slug format. | Use lowercase letters/numbers/hyphens, 3-64 chars, no leading/trailing hyphen. |
| `cannot delete pipeline while deployments still reference it` | Active Deployment uses Pipeline. | Delete deployment or roll it back first. |
| `deployment has no pipeline_id — orphaned row` | Version-only Deployment cannot resolve a Pipeline for current prediction path. | Prefer unified Trial promotion before deploying; ensure version links back to a Trial with `fitted_pipeline_id`. |
| `prediction failed: ...` | Input rows don't match the fitted pipeline schema or preprocessing cannot handle values. | Fetch `/pipelines/{id}/input-schema` or Trial detail `input_schema`, then send feature rows without the target. |
| Alias route says no production version | RegisteredModel current version is not production/current. | Promote a version to production with `set_current` or rollback endpoint, then deploy it. |

## LLM advisories

| Symptom | Likely cause | Fix |
|---|---|---|
| `No LLM provider configured + enabled` | No active provider row. | Admin calls `PUT /workspaces/{id}/llm/settings`, then `POST /llm/test-connection`. |
| Provider SDK import error | Optional SDK missing. | Install the relevant LLM extra/provider package. |
| Dataset/experiment advisory rejects non-CSV | v1 advisory prompt reads CSV-upload profile only. | Upload/materialize a CSV DataSource. |
| Explain rejects queued/running Run | Explain requires terminal state. | Wait for Run completion. |
| Debug rejects succeeded Run | Debug endpoint is for `failed` Runs only. | Use `/llm/explain-run` for succeeded/cancelled terminal Runs. |
| Advisory returns `502` but consultation appears in history | Router persisted the error audit row before raising. | Inspect `/llm/consultations/{id}` and provider logs; retry after fixing provider/key/schema. |

## Schedules, workers, webhooks, and monitoring

| Symptom | Likely cause | Fix |
|---|---|---|
| Schedule create rejects interval | `interval_seconds` must be at least `30`. | Use a larger interval or a cron expression. |
| Schedule target rejected | Kind-specific target does not belong to workspace or has wrong type. | `drift_monitor`/`batch_predict` target Deployment; `retrain` target Experiment; `dataset_refresh` target DataSource; `drift_check` target workspace id. |
| `run-now` says no handler | Schedule kind has no registered handler. | Use a supported kind or add a scheduler handler. |
| Webhook delivery does not affect original action | Intentional best-effort delivery. | Inspect webhook `last_status_code` and `last_error`; delivery failures are swallowed so runs/deployments are not corrupted. |
| HMAC verification fails downstream | Wrong secret or body mismatch. | Verify `X-PyCaret-Signature` as HMAC-SHA256 over the raw request body using the shared secret. |
| Alert email returns not configured | SMTP settings missing. | Set `PYCARET_SMTP_*` or use Slack/webhook destinations. |

## GPU queue caveats

CPU is the verified required backend for the generated PyCaret repo skill. CUDA
hardware may exist but is optional unless a future task explicitly selects GPU
model-stack verification.

| Symptom | Likely cause | Fix |
|---|---|---|
| Jobs accumulate in `gpu` queue | Run requested GPU but no worker can claim GPU jobs. | Start a worker with GPU visibility and `--queues gpu,default`, or submit with CPU/default queue. |
| CPU worker repeatedly releases GPU Job | `_can_run_job` sees no GPU (`CUDA_VISIBLE_DEVICES=""`, no NVML, no `nvidia-smi`). | Run a GPU-capable worker or change plan/setup queue. |
| `/admin/system` shows no GPU despite host GPU | API process cannot see the device. | Check container/runtime GPU pass-through and `CUDA_VISIBLE_DEVICES`. |
| GPU-specific training fails after dispatch | Queue routing only proves device visibility, not every model's GPU dependency. | Install model-specific GPU dependencies and verify in the worker environment; otherwise use CPU models. |

## Backup/restore API cautions

- `GET /api/v1/admin/backup` streams a tarball with `database.json` and raw
  files under `artifacts/`.
- `POST /api/v1/admin/restore` wipes DB tables and artifact dir before loading
  the tarball. It refuses existing data unless multipart form field
  `confirm=true` is passed.
- Coordinate database and object-store backups. Metadata without artifacts (or
  artifacts without metadata) leaves deployments and downloads broken.
