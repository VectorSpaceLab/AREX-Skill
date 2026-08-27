---
name: plexe
description: "Route Plexe model-building, retraining, and dashboard workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Plexe

Use this skill for the Plexe repository: the automated model-building pipeline, retraining flow,
package artifacts, and the Streamlit dashboard that inspects saved runs.

## What this skill covers

- Build an ML model from a natural-language intent and a dataset.
- Resume or steer a checkpointed run with feedback or model filters.
- Retrain an existing packaged model on fresh data.
- Inspect experiment workdirs and launch the dashboard for saved runs.
- Understand Plexe's config, storage, Spark, and packaging surfaces.

## Quick install

- Core runtime: `pip install plexe`
- Full local workflow: `pip install "plexe[pyspark,aws,catboost,lightgbm,pytorch]" streamlit plotly`
- Python support: 3.10 through 3.12

## Main entry points

Minimal verification after install: `python -m plexe.main --help`.

- `python -m plexe.main --train-dataset-uri ... --intent "..."`
- `from plexe.main import main`
- `python -m plexe.viz --work-dir ./workdir`

## Route map

### [model-building](sub-skills/model-building/SKILL.md)
Use this route for the main Plexe workflow:

- CLI and Python API usage
- checkpointed model building and resume flows
- retraining packaged models
- Spark local or Databricks execution
- S3-backed artifact handling
- model package contents and inference artifacts
- config, dataset, and validation questions
- workflow failures, optional dependency gaps, and packaging issues

Read the bundled references when you need the concrete CLI flags, API signatures,
phase breakdown, data formats, or troubleshooting details.

### [dashboard](sub-skills/dashboard/SKILL.md)
Use this route for dashboard and artifact inspection:

- `python -m plexe.viz`
- workdir discovery and checkpoint browsing
- dashboard tabs and model package inspection
- interpreting saved experiment metadata
- diagnosing malformed or incomplete run directories

Read the bundled dashboard reference when you need the workdir layout or tab-by-tab
behavior.

## Shared helpers

- [`references/repo-provenance.md`](references/repo-provenance.md) records the source snapshot.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) supports router import.
- [`references/troubleshooting.md`](references/troubleshooting.md) covers cross-cutting install,
  backend, and provider issues.
- [`scripts/check_env.py`](scripts/check_env.py) smoke-checks the installation.
- [`scripts/inspect_workdir.py`](scripts/inspect_workdir.py) summarizes saved Plexe runs.

## When to choose this skill

Choose Plexe when the request mentions any of these signals:

- `plexe.main`, `plexe.viz`, `python -m plexe.main`, or `python -m plexe.viz`
- `build_model`, `retrain_model`, `WorkflowIntegration`, `StandaloneIntegration`
- `work_dir/model`, `model.tar.gz`, checkpoints, or `.build/reports`
- `spark-mode local`, `spark-mode databricks`, or S3-backed artifact storage
- model search, baseline building, packaging, or dashboard inspection

If you only need a filesystem summary of a saved run, start with the dashboard route.
If you need concrete workflow steps or flags, start with model-building.
