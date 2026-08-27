# Run lifecycle

The Control Plane separates a user's action from the candidate pipelines it
creates:

- **Experiment**: persistent configuration (`task`, `target`, `setup_params`,
  optional `data_source_id`) under a Project.
- **Run**: one user-visible click/action such as setup, create, compare, or
  search. The Run stores an immutable `snapshot` of inputs and aggregate status.
- **Trial**: one candidate fitted pipeline inside a Run. Trials own their
  metrics, status, artifact URI, params, rank, notes, and promotion back-link.
- **Job**: one queueable unit of work. Trial-Jobs execute one model candidate;
  worker Jobs also handle batch prediction, dataset refresh, drift checks, Git
  publish, and retrain.
- **Event**: append-only engine event persisted for a Run and broadcast through
  the WebSocket broker.

## Submit path: `POST /experiments/{id}/runs`

`dispatch_run(db, experiment, payload, user_id=...)` performs the main server
side work:

1. Validate `payload.plan` is one of `setup`, `create`, `compare`, `search`.
2. Require `model_id` when `plan="create"`.
3. Require one data input: `sklearn_dataset`, `data_inline`, or
   `data_source_id`.
4. If `data_source_id` is used, resolve the `DataSource`, ensure it belongs to
   the experiment's workspace, and require `kind="csv_upload"` for training.
5. Compute `effective_target = payload.target or experiment.target`.
6. Persist a queued Run with a snapshot containing:
   - task, target, setup params, plan, model id, plan params,
   - sklearn dataset name, inline row count or data source id/path,
   - `triggered_by` (`user`, `schedule`, etc.) and optional trigger id.
7. Write best-effort lineage edges: experiment → run and data_source → run.
8. Decompose into Trials and Jobs, or submit the setup-only legacy path.

### Data inputs

Supported built-in sklearn datasets are `iris`, `wine`, `breast_cancer`, and
`diabetes`. They are useful for tests and demos because they require no network
access.

`data_inline` is a non-empty list of row dicts. It becomes a pandas DataFrame.

`data_source_id` currently trains only from `csv_upload` DataSources with a
stored local/file path in config. Other sources can be profiled or versioned by
DataSource drivers, but run dispatch rejects them until materialization support
is added.

## Plan behavior

### `setup`

No Trials are created. The API builds a `RunSpec` and submits it to the
in-process `RunOrchestrator` path. The worker loads data, builds the correct
PyCaret task experiment, attaches `DBEventLogger`, calls `fit(df)`, records
events, and marks the Run `succeeded` or `failed`.

Use this for fast validation of dataset + setup params.

### `create`

Creates one Trial (`kind="manual"`) and one Job (`kind="trial"`). The Trial-Job
runs `create_model(model_id)` after fitting the experiment. `model_id` is
required.

Typical body:

```json
{
  "plan": "create",
  "model_id": "lr",
  "sklearn_dataset": "iris",
  "plan_params": {"verbose": false}
}
```

### `compare`

Creates one Trial and Job per model id. Model ids are resolved as:

1. `plan_params.include_models` or `plan_params.include` if provided.
2. Otherwise the backend's default, CPU-safe list for the task.
3. `plan_params.exclude_models` or `plan_params.exclude` removes ids from the
   default list.

Compare defaults are trimmed to algorithms expected to work without optional
packages. For example, classification includes ids such as `lr`, `dt`, `rf`,
`et`, `ada`, `gbc`, `lda`, `qda`, `nb`, `knn`, `ridge`, and `svm`.

`include_models`, `exclude_models`, `include`, `exclude`, `n_select`, and
`queue` are dispatcher knobs and are stripped before the per-Trial
`create_model` call.

### `search`

Creates a variant × model grid. Each combination becomes a Trial
(`kind="tuned"`) and Trial-Job. `plan_params` supports:

- `variants`: list of setup-param overrides. If omitted in the legacy
  orchestrator path, defaults to `{}`, `{"normalize": true}`, and
  `{"normalize": true, "transformation": true}`; the decomposed dispatcher
  uses the supplied list or `[{}]`.
- `compare_params`: compare/model selection knobs.
- `include_models` / `include`: model ids.
- `optimize`: metric hint.

Use bounded variants and explicit model includes in tests to avoid heavy search.

## Queue selection and execution backends

For create/compare/search, the dispatcher writes Jobs with:

- `kind="trial"`
- `queue`: one of `default`, `cpu-heavy`, `gpu`, `inference`
- `requested_resources={"gpu": 1}` when queue is `gpu`
- `payload`: run snapshot plus `run_id`, `trial_id`, `experiment_id`, and
  the specific `model_id`.

Queue selection:

1. `plan_params.queue` wins if it is a recognized queue.
2. Otherwise `experiment.setup_params.queue` may select a queue.
3. If `use_gpu` is true in setup params, snapshot, or plan params, queue is
   `gpu`.
4. Otherwise queue is `default`.

Execution paths:

- `PYCARET_RUNS_BACKEND=inprocess`: Trial-Jobs are submitted to the API
  process `ThreadPoolExecutor` through `RunOrchestrator.submit_trial_job`.
- `PYCARET_RUNS_BACKEND=redis`: the job id is pushed to Redis. A
  `pycaret-server worker` process dequeues, locks the DB row, checks GPU
  capability when needed, and calls the registered handler.
- If Redis enqueue fails in the dispatcher, the backend logs a warning and
  falls back to in-process execution so local dev keeps working.

A CPU-only worker releases a GPU Job back to the queue instead of failing it.
The check uses `CUDA_VISIBLE_DEVICES`, then `pynvml`, then `nvidia-smi`.

## Trial job execution

`execute_trial_job(job_id)` is shared by in-process and worker backends:

1. Load Job, Trial, and Run.
2. Mark Trial `running`; mark Run `running` on the first active Trial.
3. Merge base `setup_params` with search variant override.
4. Build the appropriate task experiment from `TaskType`:
   `classification`, `regression`, `clustering`, `anomaly`, or `time_series`.
5. Attach `DBEventLogger(run_id, experiment_id)`.
6. Load data from sklearn, inline rows, or CSV path.
7. Fit the experiment and execute a `create` plan for this Trial's model id.
8. Save the fitted pipeline through the ObjectStore at
   `runs/{run_id}/trials/{safe_model_id}.pkl`.
9. Store artifact URI, sha256, size, estimator params, metrics, and terminal
   status on the Trial.
10. Reconcile the parent Run status from all Trials.

`reconcile_run_status` sets the Run terminal state once all Trials are terminal.
Mixed succeeded/failed trials leave the Run `succeeded` so winners can still be
promoted, with the Run `error` noting failed-trial count. It also ranks
succeeded Trials and caches an aggregate leaderboard on the Run.

## Events and WebSocket protocol

Every engine event passes through `DBEventLogger.emit()`:

1. Insert an `events` row with `kind`, `message`, `payload`, `duration_ms`, and
   `emitted_at`.
2. Publish the same event dict to `event_broker` subscribers.

Event read surfaces:

```http
GET /api/v1/runs/{run_id}/events?limit=500
GET /api/v1/runs/{run_id}/events?tail=true&limit=50
GET /api/v1/runs/{run_id}/events?after_id=<event_id>
```

WebSocket surface:

```text
/api/v1/runs/{run_id}/events/ws?token=<access_token>
```

The WebSocket handler requires an access token in the query string because
browser WebSocket APIs cannot set arbitrary auth headers. It replays stored
events first. If the Run is already terminal, it sends `{"kind":"run.closed"}`
and closes. Otherwise it subscribes to live broker events and sends the same
`run.closed` sentinel at completion.

Close codes:

- `4401`: missing/invalid token or inactive user.
- `4403`: token valid but user cannot access the Run's workspace.

## Follow-on Trial actions

After a Run succeeds, users can create additional Trials inside the same Run:

| Endpoint | Source | Result kind | Notes |
|---|---|---|---|
| `POST /runs/{run_id}/trials/{trial_id}/tune` | One source Trial | `tuned` | Body knobs: `n_iter`, `optimize`, `fold`, `round`. |
| `POST /runs/{run_id}/trials/{trial_id}/ensemble` | One source Trial | `ensembled` | Body `method` is `Bagging` or `Boosting`; optional `n_estimators`, `fold`. |
| `POST /runs/{run_id}/blend` | At least two source Trials | `blended` | Body `{source_trial_ids, method?, weights?, fold?}`. |
| `POST /runs/{run_id}/stack` | At least two source Trials | `stacked` | Body `{source_trial_ids, meta_model?, fold?}`. |

The orchestrator rebuilds the experiment from the source Run snapshot, reloads
source pickles through ObjectStore, calls the engine verb, saves a new Trial
artifact, and emits success/failure events into the existing Run stream.

## Artifact and storage flow

The ObjectStore abstraction hides local-vs-cloud storage. Application code
stores and loads bytes through `get_object_store()`:

- `PYCARET_STORAGE_BACKEND=local`: stores under `PYCARET_ARTIFACT_DIR`, returns
  `file://...` URIs.
- `s3` or `minio`: uses an S3-compatible client and returns `s3://bucket/key`.

Trial artifacts are saved as cloudpickle blobs. Parameters are extracted from
the final estimator with non-JSON values converted to `repr`.

Download route behavior:

- Local/file storage: stream the pickle through `FileResponse`.
- Non-file storage: redirect to a presigned URL if the ObjectStore can provide
  one.
- Missing local file: `410 GONE`.

## Promotion, registry, deployment, prediction

### Preferred promotion path

```http
POST /api/v1/runs/{run_id}/trials/{trial_id}/promote
Content-Type: application/json

{"name": "iris-prod", "description": "baseline", "tags": ["baseline"]}
```

Requirements:

- Trial status is `succeeded`.
- Trial has `stored_path` and `sha256`.
- `name` is required.

Side effects in one transaction:

1. Create a `Pipeline` row. Re-promoting the same name in the workspace bumps
   `version` and reuses the pipeline family id.
2. Find or create `RegisteredModel(workspace_id, name)`.
3. Create immutable `RegisteredModelVersion` with run/trial lineage, artifact
   URI, sha, params, metrics, and status `staging`.
4. Set `RegisteredModel.current_version_id` to the new version.
5. Set `Trial.fitted_pipeline_id`.
6. Best-effort lineage edge: run → registered_model_version.

Un-promote with `DELETE /runs/{run_id}/trials/{trial_id}/promote`. It refuses if
any Deployment still references the Pipeline or RegisteredModelVersion.

### Legacy run promotion

`POST /api/v1/runs/{run_id}/promote` promotes the Run-level artifact if present
or the best Trial artifact otherwise. It creates a Pipeline but may not create a
governed RegisteredModelVersion. Prefer the Trial promotion endpoint for new
flows.

### Deployment

Deploy from Pipeline:

```http
POST /api/v1/pipelines/{pipeline_id}/deployments
Content-Type: application/json

{"endpoint_slug": "iris-v1", "auth_mode": "workspace"}
```

Deploy from RegisteredModelVersion:

```http
POST /api/v1/registered-models/{model_id}/versions/{version_id}/deployments
Content-Type: application/json

{"endpoint_slug": "iris-v1", "auth_mode": "workspace"}
```

A deployment is version-pinned. Rollback explicitly repoints it to another
Pipeline in the same family/name and evicts the in-memory cache so the next
prediction reloads the new bytes.

### Prediction

```http
POST /api/v1/deployments/{endpoint_slug}/predict
Content-Type: application/json

{"rows": [{"sepal length (cm)": 5.1, "sepal width (cm)": 3.5,
           "petal length (cm)": 1.4, "petal width (cm)": 0.2}]}
```

The in-process `DeploymentRegistry` loads the pipeline on first request, caches
by endpoint slug and artifact path, calls `.predict()`, attaches probabilities
when available, records latency percentiles, writes a `PredictionLog`, and emits
monitoring `MetricPoint` rows.

Alias prediction:

```text
POST /api/v1/inference/{workspace_id}/{model_name}/predict
```

This resolves the RegisteredModel's `current_version_id`, finds the newest
active Deployment for that version, then delegates to the same prediction
implementation. It fails with clear `404` messages if the model, production
version, or active deployment is missing.

## Minimal programmatic lifecycle

Use this sequence for client integrations:

1. Bootstrap or login; keep `access_token`.
2. `GET /workspaces`; select `workspace_id`.
3. `POST /workspaces/{workspace_id}/projects`.
4. `POST /projects/{project_id}/experiments` with task, target, and fast setup
   params such as `{"session_id": 42, "fold": 2, "verbose": false}`.
5. `POST /experiments/{experiment_id}/runs` with a bounded plan and dataset.
6. `POST /runs/{run_id}/wait?timeout_s=...` or watch WebSocket.
7. `GET /runs/{run_id}/trials`; choose a succeeded Trial.
8. `POST /runs/{run_id}/trials/{trial_id}/promote`.
9. `POST /pipelines/{pipeline_id}/deployments` or deploy from the registry
   version returned by promotion.
10. `POST /deployments/{endpoint_slug}/predict`.

The bundled `scripts/run_lifecycle_smoke.py` automates steps 1-6 safely in a
temporary database.
