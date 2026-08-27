---
name: tracking-and-registry
description: "Use this MLflow sub-skill for experiment tracking, runs, params,
  metrics, tags, artifacts, datasets, search, tracking URI and store setup,
  fluent API versus MlflowClient decisions, and model registry workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tracking and Registry

## Use This When

- Building or debugging MLflow experiment tracking with experiments, runs, params, metrics, tags, inputs, datasets, or artifacts.
- Choosing between the fluent `mlflow.*` tracking API and `mlflow.MlflowClient` / `mlflow.tracking.MlflowClient` for explicit CRUD workflows.
- Configuring local SQLite, HTTP, Databricks, legacy file-store opt-out, or other supported tracking and registry URIs.
- Searching runs, experiments, logged models, registered models, or model versions.
- Registering a logged model, managing registered model versions, tags, descriptions, aliases, and stage-compatible lifecycle operations.

## Route Elsewhere

- Model flavor logging, model signatures, `MLmodel` contents, packaging, loading, and prediction belong in `models-and-flavors`.
- Starting or securing tracking servers, auth, deployment, projects, and serving belong in `serving-and-projects`.
- Traces, prompts, GenAI evaluation datasets, trace locations, and prompt registry work belong in `genai-observability`.

## Start Here

1. Read `references/api-reference.md` for exact entry points, URI behavior, search syntax, and registry capabilities.
2. Read `references/workflows.md` for copy-ready tracking and registry patterns.
3. Read `references/troubleshooting.md` when repairing active-run, async logging, artifact URI, search, registry, workspace, or Databricks credential failures.
4. Run `scripts/tracking_smoke.py --help`, then `python scripts/tracking_smoke.py` to verify that the installed `mlflow` package can track locally without any source checkout.

## Key Decision Rules

- Use the fluent API for in-process training code where an active run is natural; use `MlflowClient` when operating on explicit experiment IDs, run IDs, registry names, pages, or lifecycle actions.
- Set `mlflow.set_tracking_uri(...)` before starting runs. It does not move an already-active run to a new store.
- For local smoke and registry work, prefer a SQLite tracking URI such as `sqlite:///mlflow.db`; MLflow 3 places filesystem tracking backends in maintenance mode unless `MLFLOW_ALLOW_FILE_STORE=true` is deliberately set.
- Keep tracking URI and registry URI separate in debugging: `MlflowClient(registry_uri=...)` and `mlflow.set_registry_uri(...)` can target a different registry than the tracking backend.
- Treat Databricks tracking URIs specially: registry URI defaults toward Unity Catalog (`databricks-uc`) unless explicitly overridden.
