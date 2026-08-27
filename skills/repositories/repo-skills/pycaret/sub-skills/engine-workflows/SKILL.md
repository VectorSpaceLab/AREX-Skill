---
name: engine-workflows
description: "Guides PyCaret 4.0 engine workflows in notebooks and scripts using
  OOP task classes, typed results, event logging, introspection, persistence,
  plotting, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PyCaret Engine Workflows

Use this sub-skill when the task is about running the PyCaret 4.0 Python engine directly from notebooks, scripts, tests, or small local experiments.

## Route here for

- OOP-only task classes: `ClassificationExperiment`, `RegressionExperiment`, `ClusteringExperiment`, `AnomalyExperiment`, and `TimeSeriesExperiment`.
- Engine verbs: `fit`, `create_model`, `compare_models`, `tune_model`, `predict_model`, `assign_model`, `plot_model`, `evaluate_model`, `interpret_model`, `check_stats`, `automl`, and persistence.
- Typed result handling: `CreateResult`, `CompareResult`, `TuneResult`, `PredictResult`, and related dataclasses.
- Structured event logging with `pycaret.logging.MemoryLogger` and JSONL event capture.
- Engine introspection with `pycaret.api` and runtime model/metric registries.
- Safe CPU smoke checks using bundled scripts.

## Route elsewhere

- FastAPI server, run orchestration, REST routes, auth, deployments, LLM advisories, and `pycaret-server` CLI usage: use `../control-plane-api/SKILL.md`.
- React/Vite control-plane UI changes: use `../web-ui/SKILL.md`.
- Docker, deployment operations, secret persistence, queues, and GPU worker routing: use `../platform-operations/SKILL.md`.
- Contributor policy, release notes, tests, kill-list, and repository editing conventions: use `../repo-development/SKILL.md`.

## First-read references

1. Read [references/model-and-task-overview.md](references/model-and-task-overview.md) to choose the task class, optional extras, model IDs, metrics, and validation scope.
2. Read [references/api-reference.md](references/api-reference.md) for verified signatures, result fields, event APIs, and introspection APIs.
3. Read [references/workflows.md](references/workflows.md) for concrete recipes for each task family, persistence, plots, events, and sample-data patterns.
4. Read [references/troubleshooting.md](references/troubleshooting.md) when a workflow fails or a user request resembles PyCaret 3.x functional API usage.

## Short workflow

1. Install an engine environment with the required extras for the selected task. CPU is sufficient for the verified engine workflows. GPU model stacks are optional and were not required for this skill.
   - Core tabular classification/regression/clustering: `pip install pycaret`
   - Anomaly detection: `pip install "pycaret[anomaly]"`
   - Time series: `pip install "pycaret[timeseries]"`
   - SHAP interpretation: `pip install "pycaret[interpret]"`
   - Static image export for Plotly: `pip install "pycaret[export]"`
2. Import task classes only from `pycaret.tasks` or compatibility class exports such as `pycaret.classification.ClassificationExperiment`; do **not** use removed functional helpers such as `setup()` or module-level `compare_models()`.
3. Build an experiment object, call `.fit(...)`, then use typed result fields instead of `pull()` as the primary data path:

   ```python
   from pycaret.tasks import ClassificationExperiment

   exp = ClassificationExperiment(target="target", session_id=42, fold=3, n_jobs=1).fit(df)
   compare = exp.compare_models(include=["lr", "dt"], n_select=2, verbose=False)
   best = compare.best
   tuned = exp.tune_model(best, n_iter=3, verbose=False).pipeline
   predictions = exp.predict_model(tuned).predictions
   leaderboard = compare.leaderboard
   ```

4. Validate the environment or task route with the bundled scripts:

   ```bash
   python scripts/engine_smoke.py --help
   python scripts/engine_smoke.py --task classification --list-models
   python scripts/engine_smoke.py --task all
   python scripts/introspection_snapshot.py --task classification --task regression
   ```

5. For failures, use [references/troubleshooting.md](references/troubleshooting.md) before changing API style, adding broad extras, or assuming a GPU/backend issue.

## Script ownership

- [scripts/engine_smoke.py](scripts/engine_smoke.py): no-network smoke runner using sklearn toy data or tiny inline frames; supports `--task classification|regression|clustering|anomaly|time-series|all` and `--list-models`.
- [scripts/introspection_snapshot.py](scripts/introspection_snapshot.py): prints a JSON snapshot from `pycaret.api` for selected tasks.

## Operating constraints

- PyCaret 4.0 is OOP-only for engine usage. Do not reintroduce the 3.x functional/global-current-experiment pattern.
- CPU is the required backend for this skill. CUDA hardware may exist, but GPU model-stack verification is optional and outside this sub-skill's required path.
- `pycaret.datasets.get_data(...)` can perform network reads. Public examples in this sub-skill prefer sklearn built-in toy data or inline frames for no-network reproducibility.
- `setup_kwargs` passed into `.fit(..., **kwargs)` are unsupported in PyCaret 4.0 and raise `ConfigurationError`; use constructor parameters or request a first-class parameter.
