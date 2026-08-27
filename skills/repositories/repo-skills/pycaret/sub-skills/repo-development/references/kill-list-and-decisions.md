# Kill List And Decisions

The kill list and ADR log are settled project evidence. Use them before implementing features, restoring PyCaret 3.x behavior, adding dependencies, or changing architecture.

## Decision order

1. Check whether the request is directly on the kill list.
2. Check whether it is a re-skinned version of a killed feature.
3. Check ADRs for the same domain.
4. If the request conflicts, stop and explain the conflict. Ask the maintainer to explicitly change scope before implementing.
5. If the request is adjacent but plausibly new, propose an alternative that preserves PyCaret 4 architecture.

## Removed dependency families

The following dependencies were deliberately removed from the engine/core surface and should not be reintroduced casually:

| Removed | Replacement / stance |
| --- | --- |
| `mlflow`, `comet-ml`, `wandb`, `dagshub` | Use the lean structured event logger in `pycaret.logging`; external tracker adapters are out of core unless a future ADR says otherwise. |
| `fugue`, `dask`, `distributed`, `ray[tune]`, `tune-sklearn` | No core replacement. Distributed AutoML is V3 opt-in, not current engine core. |
| `yellowbrick`, `mljar-scikit-plot` | Plotly plot modules in `pycaret.plots.*`. |
| `schemdraw`, `plotly-resampler` | Dropped or evaluate only if a clear future need exists. |
| `evidently` | Engine `check_drift` removed; Control Plane drift monitoring owns drift. |
| `fairlearn` | Engine `check_fairness` removed. |
| `ydata-profiling` / `pandas-profiling` | UI/data-source profiling owns EDA; engine `eda` removed. |
| `explainerdashboard`, `gradio` | React Control Plane replaces dashboard/app helpers. |
| `fastapi`, `uvicorn` in the engine | Server lives in separate `pycaret-server`; engine stays a library. |
| `boto3`, `moto` in the engine | Engine AWS/S3 deploy helpers removed; platform/storage connectors belong in server/ops. |
| `m2cgen` | `convert_model` removed. |
| `flask`, `Werkzeug`, `dash[testing]` | Removed with dashboard/parallel surfaces. |
| `setuptools` as a runtime dependency | Build uses hatchling; runtime should not need setuptools. |

Some optional dependencies remain valid in explicit extras, such as `pyod` for anomaly, `sktime`/`statsmodels`/`pmdarima` for time series, `shap` for `[interpret]`, and server extras for provider-specific/DB/storage functionality. Do not confuse valid optional extras with killed core dependencies.

## Removed public engine APIs

Do not restore these PyCaret 3.x public helpers in the engine:

- `create_api()`
- `create_app()`
- `create_docker()`
- `dashboard()`
- `check_drift()`
- `check_fairness()`
- `deploy_model()` for AWS/S3 deployment
- `eda()` profiling wrapper
- `convert_model()`
- `parallel_backend` argument on setup/model-comparison flows
- The module-level functional API and implicit current experiment state
- Legacy `TSForecastingExperiment` import alias; use `TimeSeriesExperiment`

The modern preserved notebook path is OOP-based and typed. If a user wants a removed 3.x helper, recommend the current 4.x surface or a separate package/integration rather than restoring tech debt.

## Features explicitly preserved or revived

Do not overstate removals. Current PyCaret 4 includes OOP versions of the golden path and revived diagnostic verbs:

- Task classes: `ClassificationExperiment`, `RegressionExperiment`, `ClusteringExperiment`, `AnomalyExperiment`, `TimeSeriesExperiment`.
- Core workflows: `fit`, `create_model`, `compare_models`, `tune_model`, `predict_model`, `finalize_model`, supervised ensemble/blend/stack/calibrate where supported, unsupervised `assign_model`.
- Revived verbs in the verified source: `plot_model`, `evaluate_model`, `interpret_model`, `automl`, `get_leaderboard`, `TimeSeriesExperiment.check_stats`.
- Persistence: `save_model`, `load_model`.
- Introspection: `pycaret.api.list_models`, `describe_model`, `list_metrics`, `describe_setup_params`.
- Structured logging: `pycaret.logging.BaseLogger`, `MemoryLogger`.

## ADR highlights that affect maintainer choices

The ADR log is newest-first. Important settled decisions include:

### Unified promote writes Pipeline + RegisteredModelVersion

Promotion is a single atomic endpoint that writes both the serving artifact pointer (`Pipeline`) and governance row (`RegisteredModelVersion`). Do not reintroduce parallel promote paths or a standalone broken registry-version creation flow.

### APScheduler in-process, not Celery/RQ/Arq for V1 schedules

Scheduled drift/retrain jobs use APScheduler inside the FastAPI process. Redis-backed queues are deferred; do not add Celery/RQ/Arq just to satisfy current V1 scheduling.

### Pipeline rollback uses `family_id`

Pipeline revisions share a `family_id`; rollback requires the target pipeline to share the current deployment family. Do not switch to linked-list parent pointers without a new ADR.

### Fernet first for secrets

At-rest secrets use `cryptography.fernet.Fernet` with `PYCARET_SECRETS_KEY` and `ENC:v1:` prefix. KMS/Vault wrapping is V2. Do not store new secrets in plaintext or add cloud SDKs as core requirements for local self-hosting.

### Dedicated UI pages for V2 features

Schedules, Templates, Webhooks, and Admin have dedicated workspace routes. Avoid burying substantial features in a mega Settings tab.

### Trials table over leaderboard JSON

Every successful run persists first-class `Trial` rows in addition to legacy JSON. UI reads trials. Do not build new UI features by parsing only `Run.leaderboard` unless compatibility requires it.

### FSL licensing posture

The engine and public site use FSL-1.1-MIT for 4.x, with future MIT conversion. Platform packages are dual-licensed. Do not change legal files or license posture without maintainer/legal approval.

### Claude-Code-first contributor flow

No CI bot auto-fixes issues using maintainer-paid LLM keys. Contributors run agents locally and open PRs. Do not add an auto-fixing GitHub Action or repository `ANTHROPIC_API_KEY` workflow.

### Monorepo structure is canonical

Use `apps/`, `services/`, `packages/`, and `infra/`. Do not flatten `pycaret-server` or `pycaret-ui` back to root.

### LLM router abstraction

LLM calls go through provider abstractions. Do not import `anthropic` or `openai` directly outside the provider layer.

### Functional API deleted wholesale

The OOP API is the 4.0 contract. Do not add compatibility shims for `pycaret.classification.setup(...)` or implicit global state.

### Event-stream logger in-process, not tracker adapter

Structured events are the core integration point. External trackers are not core dependencies.

### Typed dataclass returns

Public verbs return typed dataclasses, not bare estimators/DataFrames/dicts. Any new public verb follows this pattern.

## How to respond to restore requests

Use this pattern:

1. Acknowledge the requested feature.
2. State whether it is killed, adjacent to killed, or allowed.
3. Quote the settled rationale in plain language.
4. Offer the current PyCaret 4 alternative.
5. If there is no alternative and the maintainer still wants it, ask for explicit scope approval and an ADR before implementation.

Example:

> `deploy_model()` for AWS/S3 is on the PyCaret 4 kill list. The engine no longer ships cloud deploy helpers or `boto3`; deployment lives in the Control Plane server and operations layer. For a local library workflow use `save_model()` / `load_model()`. For serving use `pycaret-server` deployments. Re-adding engine AWS deployment would require maintainer approval and a new ADR because it reverses a settled dependency cut.

## Dependency additions

Before adding any dependency:

- Confirm it is not on the kill list.
- Decide whether it belongs in engine core, an engine optional extra, server core, server extra, UI dependency, or dev/test only.
- Prefer optional extras for model-family, provider, storage, and interpretation dependencies.
- Avoid upper-bound pins on NumPy/pandas/scipy/sklearn/joblib unless a documented compatibility block exists.
- Add/update tests that prove lazy import and missing-extra error behavior.
- Add `DEPS` release notes and an ADR for new top-level runtime dependency scope.

## Quick classifier

For a pasted issue title/body, run the bundled helper for a first-pass signal:

```bash
python skills/disco/pycaret/sub-skills/repo-development/scripts/classify_issue_text.py \
  --title "MLflow logging fails" \
  --body "setup(log_experiment=True) errors with mlflow..."
```

Treat the output as triage assistance, not a substitute for reading the kill list and ADRs.
