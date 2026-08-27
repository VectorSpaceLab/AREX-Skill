# Control Plane API reference

All application routers are mounted under `/api/v1` by the FastAPI app factory.
The root metadata and health endpoints stay outside that prefix:

- `GET /` → `{app, version, docs, openapi}`.
- `GET /healthz` → `{ok: true}`.
- `GET /docs`, `GET /redoc`, `GET /openapi.json` expose Swagger, ReDoc, and
  the machine-readable schema.

## Authentication and authorization

### First-run bootstrap

1. Check whether setup is needed:

   ```http
   GET /api/v1/setup/status
   ```

   Response: `{is_bootstrapped: bool, user_count: int, workspace_count: int}`.

2. Bootstrap once:

   ```http
   POST /api/v1/setup/bootstrap
   Content-Type: application/json

   {
     "email": "admin@example.com",
     "password": "supersecret",
     "display_name": "Admin",
     "workspace_name": "Default"
   }
   ```

   This creates a superuser, workspace, and `WorkspaceMember(role="admin")`,
   then returns `{access_token, refresh_token, token_type, expires_in}`. A
   second bootstrap returns `409 instance already bootstrapped`.

### Tokens and API keys

Protected routes accept either:

- `Authorization: Bearer <access_token>` from `/auth/login` or `/setup/bootstrap`.
- `X-PyCaret-Key: <pck_...>` for programmatic access. Bearer JWT wins if both
  are present.

Auth endpoints:

| Method | Path | Body / purpose |
|---|---|---|
| `POST` | `/api/v1/auth/login` | `{email, password}` → access/refresh pair. |
| `POST` | `/api/v1/auth/refresh` | `{refresh_token}` → rotated access/refresh pair. Old refresh is revoked. |
| `POST` | `/api/v1/auth/logout` | `{refresh_token}` → revokes that refresh token, `204`. |
| `GET` | `/api/v1/auth/me` | Current user. Use this instead of `/setup/me` (`501`). |
| `POST` | `/api/v1/auth/api-keys` | `{name, workspace_id?, expires_in_days?, scopes?}` → plaintext token returned once. |
| `GET` | `/api/v1/auth/api-keys` | Current user's keys, no plaintext. |
| `DELETE` | `/api/v1/auth/api-keys/{key_id}` | Soft-revoke a key. |

Workspace access is membership-based. Superusers can see all workspaces.
Workspace admin-equivalent roles are `owner`, `admin`, and `project_admin`.
General member reads use `_require_access`; writes that need administrative
control use `_require_admin`.

## Domain model quick map

- Identity: `User`, refresh-token `Session`, programmatic `ApiKey`.
- Tenancy: `Workspace`, `WorkspaceMember`, `Project`.
- Experiment setup: `Experiment` stores `task`, `target`, `setup_params`, and
  optional `data_source_id`.
- Data catalog: `DataSource`, `Connection`, encrypted `Secret`, versioned
  `Dataset`, and append-only `Lineage` edges.
- Execution: `Run` is one user-visible action; `Trial` is one candidate
  pipeline inside a Run; `Job` is a queueable worker unit; `Event` is the
  persisted engine event stream; `Artifact` and `FoldMetric` are run outputs.
- Model/deployment: legacy `Pipeline`, governed `RegisteredModel` and
  immutable `RegisteredModelVersion`, `Deployment`, `PredictionLog`,
  `MetricPoint`, `DriftReport`, and `AlertRule`.
- Advisory and automation: `LLMProviderSetting`, `LLMConsultation`,
  `ScheduledJob`, `WebhookSubscription`, `ApprovalWorkflow`, `AuditLog`,
  `ExperimentTemplate`, `GitRepository`, `Notebook`, and `Analysis`.

Common statuses:

- Run: `queued`, `running`, `succeeded`, `failed`, `cancelled`.
- Trial: `queued`, `running`, `succeeded`, `failed`, `cancelled`.
- Job: `queued`, `running`, `succeeded`, `failed`, `cancelled`.
- Deployment: `active`, `paused`, `archived`.
- Registered model version: `staging`, `production`, `archived`.
- Approval: `pending`, `approved`, `rejected`, `executed`, `cancelled`.

## Route families

### Workspace, membership, project, experiment

| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/v1/workspaces` | Visible workspaces. |
| `POST` | `/api/v1/workspaces` | `{name, description?}`; creator becomes admin. |
| `GET` | `/api/v1/workspaces/{workspace_id}` | Requires membership. |
| `DELETE` | `/api/v1/workspaces/{workspace_id}` | Workspace admin. |
| `GET` | `/api/v1/workspaces/{workspace_id}/members` | Member list. |
| `POST` | `/api/v1/workspaces/{workspace_id}/members` | Invite/add member. |
| `PATCH` | `/api/v1/workspaces/{workspace_id}/members/{user_id}` | Change role. |
| `DELETE` | `/api/v1/workspaces/{workspace_id}/members/{user_id}` | Remove member. |
| `GET` | `/api/v1/workspaces/{workspace_id}/projects` | List projects. |
| `POST` | `/api/v1/workspaces/{workspace_id}/projects` | `{name, description?, tags?}`. |
| `GET` | `/api/v1/workspaces/{workspace_id}/projects/{project_id}` | Fetch one project. |
| `DELETE` | `/api/v1/workspaces/{workspace_id}/projects/{project_id}` | Delete project. |
| `GET` | `/api/v1/projects/{project_id}/experiments` | List experiments. |
| `POST` | `/api/v1/projects/{project_id}/experiments` | `{name, task, target?, setup_params?, data_source_id?}`. |
| `GET` | `/api/v1/projects/{project_id}/experiments/{experiment_id}` | Includes run stats. |
| `DELETE` | `/api/v1/projects/{project_id}/experiments/{experiment_id}` | Delete experiment. |

`ExperimentCreate.task` must be one of `classification`, `regression`,
`clustering`, `anomaly`, or `time_series`.

### Engine introspection proxy

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/describe/models?task=classification` | Model cards for a task. |
| `GET` | `/api/v1/describe/models/{model_id}?task=classification` | One model card. |
| `GET` | `/api/v1/describe/metrics?task=classification` | Task metrics. |
| `GET` | `/api/v1/describe/setup-params?task=classification` | Dynamic setup form schema. |

Route engine-model semantics to `engine-workflows`; this backend surface only
proxies and serializes the introspection data.

### Runs, trials, and events

Submit a run:

```http
POST /api/v1/experiments/{experiment_id}/runs
Content-Type: application/json

{
  "plan": "create",
  "model_id": "lr",
  "sklearn_dataset": "iris",
  "plan_params": {"verbose": false}
}
```

`RunCreate` fields:

- `plan`: `setup`, `create`, `compare`, or `search`.
- `model_id`: required for `plan="create"`.
- `plan_params`: dict of plan-specific knobs.
- Exactly one input source should be supplied: `sklearn_dataset`, `data_inline`,
  or `data_source_id`.
- `target`: optional override when the experiment or data source does not carry
  a target.

Important run/trial routes:

| Method | Path | Notes |
|---|---|---|
| `POST` | `/api/v1/experiments/{experiment_id}/runs` | Returns `202` with a queued Run. |
| `GET` | `/api/v1/experiments/{experiment_id}/runs` | Newest first. |
| `GET` | `/api/v1/runs/{run_id}` | Run status, snapshot, leaderboard, metrics summary. |
| `POST` | `/api/v1/runs/{run_id}/wait?timeout_s=30` | Block until terminal or timeout. |
| `POST` | `/api/v1/runs/{run_id}/cancel` | Cooperative cancellation. |
| `GET` | `/api/v1/runs/{run_id}/events` | Persisted events; supports `limit`, `after_id`, `tail`. |
| `WS` | `/api/v1/runs/{run_id}/events/ws?token=<access_token>` | Replays stored events, streams live events, sends `run.closed`. |
| `GET` | `/api/v1/runs/{run_id}/trials` | Trial list for this Run. |
| `GET` | `/api/v1/runs/{run_id}/trials/{trial_id}` | Trial detail, metrics, params, pipeline tree, input schema. |
| `GET` | `/api/v1/runs/{run_id}/trials/{trial_id}/download` | Trial pickle stream or presigned redirect. |
| `PATCH` | `/api/v1/runs/{run_id}/trials/{trial_id}` | Notes. |
| `POST` | `/api/v1/runs/{run_id}/trials/{trial_id}/predict` | Inference without promotion: `{rows:[...]}`. |
| `GET` | `/api/v1/runs/{run_id}/trials/{trial_id}/cv` | On-demand CV metrics for classification/regression. |
| `GET` | `/api/v1/runs/{run_id}/trials/{trial_id}/cohorts` | Cohort/slice metrics. |
| `POST` | `/api/v1/runs/{run_id}/trials/{trial_id}/tune` | Follow-on tuned Trial. |
| `POST` | `/api/v1/runs/{run_id}/trials/{trial_id}/ensemble` | Bagging/Boosting Trial. |
| `POST` | `/api/v1/runs/{run_id}/blend` | Blend at least two source trials. |
| `POST` | `/api/v1/runs/{run_id}/stack` | Stack at least two source trials. |
| `GET` | `/api/v1/experiments/{experiment_id}/trials` | Cross-run trial list; filters `kind`, `run_id`, `limit`. |
| `GET` | `/api/v1/trials/{trial_id}` | Direct trial deep link. |
| `PATCH` | `/api/v1/trials/{trial_id}` | Direct name/notes patch. |
| `DELETE` | `/api/v1/trials/{trial_id}` | Refuses promoted trials. |

### Data sources and data catalog

CSV upload is the easiest training path:

```http
POST /api/v1/workspaces/{workspace_id}/data-sources/upload
Content-Type: multipart/form-data

file=<csv>, name=iris.csv, description=optional
```

Data-source and catalog routes:

| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/v1/workspaces/{workspace_id}/data-sources` | List data sources. |
| `POST` | `/api/v1/workspaces/{workspace_id}/data-sources/upload` | CSV upload; stores checksum, columns, row count, file path. |
| `POST` | `/api/v1/workspaces/{workspace_id}/data-sources` | Register non-upload source: `s3` or `postgres`. |
| `GET` | `/api/v1/data-sources/{data_source_id}` | Fetch one source. |
| `GET` | `/api/v1/data-sources/{data_source_id}/profile?sample_rows=10` | Rich EDA profile; CSV and driver-backed sources. |
| `DELETE` | `/api/v1/data-sources/{data_source_id}` | Delete; CSV files are cleaned up. |
| `GET` | `/api/v1/workspaces/{workspace_id}/secrets` | Encrypted secret list; plaintext never returned. |
| `POST` | `/api/v1/workspaces/{workspace_id}/secrets` | `{name, kind?, value}`; encrypts value. |
| `DELETE` | `/api/v1/workspaces/{workspace_id}/secrets/{secret_id}` | Delete secret. |
| `GET` | `/api/v1/workspaces/{workspace_id}/connections` | Connection rows. |
| `POST` | `/api/v1/workspaces/{workspace_id}/connections` | `{name, kind, config, secret_id?}`. |
| `GET` | `/api/v1/workspaces/{workspace_id}/connections/{connection_id}/tables` | Driver table discovery. |
| `POST` | `/api/v1/workspaces/{workspace_id}/connections/{connection_id}/test` | Driver connectivity probe. |
| `POST` | `/api/v1/workspaces/{workspace_id}/data-sources/from-connection` | Register a table as DataSource. |
| `DELETE` | `/api/v1/workspaces/{workspace_id}/connections/{connection_id}` | Delete connection. |
| `GET` | `/api/v1/datasource-kinds` | Registered driver kinds, currently `csv_upload` and `postgres`. |
| `GET` | `/api/v1/data-sources/{data_source_id}/datasets` | Version history. |
| `POST` | `/api/v1/data-sources/{data_source_id}/refresh` | New `Dataset` version via driver introspection. |
| `GET` | `/api/v1/workspaces/{workspace_id}/lineage` | All lineage or rooted BFS with `node_kind`, `node_id`, `depth`. |

Run dispatch currently supports `data_source_id` only when the source kind is
`csv_upload`. Driver-backed sources can be profiled and versioned, but a
training Run against them needs a supported materialized CSV path or a future
worker/materialization extension.

### Pipelines, registry, deployments, serving

There are two promotion surfaces:

- `POST /api/v1/runs/{run_id}/promote` promotes a succeeded Run's legacy
  run-level/best-trial artifact to a `Pipeline` row.
- `POST /api/v1/runs/{run_id}/trials/{trial_id}/promote` is the preferred
  unified path: it creates a `Pipeline`, creates/fetches a `RegisteredModel`,
  creates an immutable `RegisteredModelVersion`, links the Trial, and records
  lineage.

Key endpoints:

| Method | Path | Notes |
|---|---|---|
| `POST` | `/api/v1/runs/{run_id}/promote` | Body `{name, description?, tags?}`; Run must be succeeded. |
| `POST` | `/api/v1/runs/{run_id}/trials/{trial_id}/promote` | Unified Pipeline + RegisteredModelVersion promotion. |
| `DELETE` | `/api/v1/runs/{run_id}/trials/{trial_id}/promote` | Un-promote if no Deployment references it. |
| `GET` | `/api/v1/workspaces/{workspace_id}/pipelines` | Pipeline list. |
| `GET` | `/api/v1/pipelines/{pipeline_id}` | Pipeline detail. |
| `GET` | `/api/v1/pipelines/{pipeline_id}/versions` | Same family/name versions. |
| `GET` | `/api/v1/pipelines/{pipeline_id}/input-schema` | Sample row and feature columns from origin run. |
| `DELETE` | `/api/v1/pipelines/{pipeline_id}` | Refuses active deployment references. |
| `GET` | `/api/v1/workspaces/{workspace_id}/registered-models` | Registry model list. |
| `POST` | `/api/v1/workspaces/{workspace_id}/registered-models` | Create named model shell. |
| `GET` | `/api/v1/registered-models/{model_id}` | Fetch model. |
| `DELETE` | `/api/v1/registered-models/{model_id}` | Refuses production versions. |
| `GET` | `/api/v1/registered-models/{model_id}/versions` | Version list. |
| `POST` | `/api/v1/registered-models/{model_id}/versions/{version_id}/promote` | Set `staging`/`production`/`archived`; archives old production. |
| `POST` | `/api/v1/registered-models/{model_id}/versions/{version_id}/request-promotion` | Open approval workflow. |
| `POST` | `/api/v1/registered-models/{model_id}/versions/{version_id}/rollback` | Make an older version current production. |
| `POST` | `/api/v1/pipelines/{pipeline_id}/deployments` | Body `{endpoint_slug, auth_mode?}`. |
| `POST` | `/api/v1/registered-models/{model_id}/versions/{version_id}/deployments` | Deploy from governed version. |
| `GET` | `/api/v1/workspaces/{workspace_id}/deployments` | List deployments. |
| `GET` | `/api/v1/deployments/{deployment_id}` | Deployment detail. |
| `DELETE` | `/api/v1/deployments/{deployment_id}` | Evicts registry cache then deletes. |
| `POST` | `/api/v1/deployments/{deployment_id}/rollback` | Body `{pipeline_id}`; same family/name required. |
| `POST` | `/api/v1/deployments/{endpoint_slug}/predict` | Version-pinned prediction. |
| `POST` | `/api/v1/inference/{workspace_id}/{model_name}/predict` | Alias route to current production version. |
| `GET` | `/api/v1/deployments/{deployment_id}/prediction-logs` | Paginated logs; `limit`, `offset`, `status_filter`. |

Deployment slug validation: `^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$`. `auth_mode`
accepts `workspace`, `api-key`, or `public`; current workspace JWT/API-key auth
is the reliable v1 path.

Prediction body:

```json
{"rows": [{"feature_a": 1, "feature_b": "x"}]}
```

Response includes deployment id, endpoint slug, per-row predictions, latency,
and request id. Predictions are logged with bounded request/response samples.

### Monitoring, drift, schedules, webhooks, governance, admin

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/deployments/{deployment_id}/metrics` | Time-series metric points; filters `metric`, `since_seconds`, `limit`. |
| `POST` | `/api/v1/deployments/{deployment_id}/metrics` | Append one metric point. |
| `GET` | `/api/v1/workspaces/{workspace_id}/alert-rules` | Alert rules. |
| `POST` | `/api/v1/workspaces/{workspace_id}/alert-rules` | `{name, metric, comparator, threshold, destination_kind, ...}`. |
| `PATCH` | `/api/v1/alert-rules/{rule_id}` | Toggle/edit threshold/window/destination. |
| `DELETE` | `/api/v1/alert-rules/{rule_id}` | Delete rule. |
| `POST` | `/api/v1/deployments/{deployment_id}/drift-reports` | Record upstream-computed drift snapshot. |
| `GET` | `/api/v1/deployments/{deployment_id}/drift-reports` | List snapshots. |
| `GET` | `/api/v1/drift-reports/{report_id}` | One drift report. |
| `GET` | `/api/v1/workspaces/{workspace_id}/schedules` | Scheduled jobs. |
| `POST` | `/api/v1/workspaces/{workspace_id}/schedules` | Kinds: `drift_monitor`, `retrain`, `drift_check`, `batch_predict`, `dataset_refresh`. |
| `GET` | `/api/v1/schedules/{job_id}` | One schedule. |
| `PATCH` | `/api/v1/schedules/{job_id}` | Update schedule/spec/enabled. |
| `DELETE` | `/api/v1/schedules/{job_id}` | Unschedule + delete. |
| `POST` | `/api/v1/schedules/{job_id}/run-now` | Fire handler synchronously. |
| `GET` | `/api/v1/workspaces/{workspace_id}/webhooks` | Webhook list. |
| `POST` | `/api/v1/workspaces/{workspace_id}/webhooks` | `{url, event_types, secret?, filters?, enabled?}`. |
| `GET` | `/api/v1/webhooks/{webhook_id}` | One webhook. |
| `PATCH` | `/api/v1/webhooks/{webhook_id}` | Edit URL/events/secret/filters/enabled. |
| `DELETE` | `/api/v1/webhooks/{webhook_id}` | Delete. |
| `POST` | `/api/v1/webhooks/{webhook_id}/test` | Synthetic delivery to that row. |
| `GET` | `/api/v1/workspaces/{workspace_id}/approvals` | Approval inbox; `status_filter`. |
| `POST` | `/api/v1/workspaces/{workspace_id}/approvals` | Open gated action. |
| `POST` | `/api/v1/approvals/{approval_id}/approve` | Add signature. |
| `POST` | `/api/v1/approvals/{approval_id}/reject` | Reject. |
| `POST` | `/api/v1/approvals/{approval_id}/execute` | Execute approved action. |
| `GET` | `/api/v1/admin/queues` | Queue depth + recent throughput. |
| `GET` | `/api/v1/admin/workers` | Workers currently holding job locks. |
| `GET` | `/api/v1/admin/system` | Runs backend, Redis health, GPU inventory, worker queues. |
| `GET` | `/api/v1/admin/users` | Superuser user list. |
| `PATCH` | `/api/v1/admin/users/{user_id}` | Superuser user patch. |
| `GET` | `/api/v1/admin/audit-logs` | Superuser audit log list. |
| `GET` | `/api/v1/workspaces/{workspace_id}/audit-logs` | Workspace audit log list. |
| `GET` | `/api/v1/admin/backup` | Stream backup tarball. |
| `POST` | `/api/v1/admin/restore` | Multipart restore; requires `confirm=true` when data exists. |

Additional route families exist for model-library sync, experiment templates,
plots, notebooks, statistical analyses, sample datasets, and Git repositories.
Use `/openapi.json` against the running server for the exact installed schema
when building a client.

## Request/response conventions

- IDs are UUID strings. Datetimes serialize as ISO strings.
- Most create routes return `201`; run submit and follow-on trial actions return
  `202`; deletes return `204`.
- Pydantic validation errors are `422`. Application validation is usually `400`.
  Missing rows return `404`; duplicate names/slugs and protected deletes return
  `409`; missing uploaded artifacts often return `410`; provider/advisory
  upstream failures are commonly `502`.
- Some list routes return a bare JSON list; newer page-oriented routes return
  `{items: [...]}`. Check the specific family before assuming one shape.
- Multipart is used for CSV upload and admin restore. Prediction and most
  lifecycle operations use JSON.
- Do not rely on local filesystem paths returned in a dev `DataSource.config` as
  a public API. Artifact-like values are moving toward opaque URIs (`file://`,
  `s3://`, `minio`/S3-compatible); read and write them through the API or
  ObjectStore abstraction where possible.

## Adding or extending a backend route

For route implementation tasks, keep the data contract and access pattern
consistent:

1. Define/adjust SQLAlchemy models and add an Alembic migration for durable
   schema changes.
2. Add Pydantic request/response schemas when the route has a stable typed
   contract; small admin routes may return dicts.
3. Put route functions under `pycaret_server.api.<module>` and mount the router
   in the app factory's `/api/v1` loop.
4. Use `CurrentUser` and `get_db`; call `_require_access`, `_require_admin`, or
   a superuser gate before touching workspace data.
5. Persist side effects in the DB first, then fan out best-effort events,
   webhooks, or cache invalidation.
6. Add a TestClient integration test using an isolated SQLite DB and temporary
   artifact directory. See [CLI and configuration](cli-and-config.md) for the
   fixture pattern.
