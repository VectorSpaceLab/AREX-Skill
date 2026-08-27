---
name: model-building
description: "Route Plexe's build, resume, retrain, and packaging workflow."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# model-building

Use this sub-skill for Plexe's main automated ML workflow: building a model from a dataset,
resuming a checkpointed run, retraining a packaged model, and reasoning about the artifacts
written into `work_dir/` and `work_dir/model/`.

## Typical triggers

- "Build a Plexe model from this dataset"
- "Resume the checkpointed run"
- "Retrain the packaged model on new data"
- "Why did Plexe choose this model type or metric?"
- "What files should exist in the final model package?"
- "How do I point Plexe at S3 or Databricks?"

## What belongs here

- `python -m plexe.main` and `from plexe.main import main`
- `plexe.workflow.build_model` and `plexe.retrain.retrain_model`
- `plexe.config.Config`, CLI flags, YAML config, and environment overrides
- `WorkflowIntegration` and `StandaloneIntegration`
- Spark local and Databricks execution
- dataset normalization, splitting, sampling, and validation
- baseline building, tree search, and checkpoint resume behavior
- training templates and packaged inference artifacts
- model package structure and retraining constraints
- cross-cutting workflow failures and recovery steps

## What stays out

- Dashboard UI, experiment browsing, and workdir visualization belong in
  [dashboard](../dashboard/SKILL.md).
- Repository maintenance, CI, and release behavior stay outside this skill.

## Read these references first when needed

- [`references/workflows.md`](references/workflows.md) for the end-to-end phase flow.
- [`references/configuration.md`](references/configuration.md) for CLI flags, config sources,
  environment variables, Spark/Databricks settings, and LLM routing.
- [`references/api-reference.md`](references/api-reference.md) for public signatures and object shapes.
- [`references/data-formats.md`](references/data-formats.md) for input formats, layouts,
  checkpoint outputs, and the packaged model tree.
- [`references/troubleshooting.md`](references/troubleshooting.md) for install, backend,
  data, retrain, and packaging failures.
- [`scripts/check_env.py`](../../scripts/check_env.py) when you need a quick install, CLI,
  dashboard, or Spark smoke check.
- [`scripts/inspect_workdir.py`](../../scripts/inspect_workdir.py) when you need a quick
  read-only summary of saved runs and packages.

## How to work this route

1. Identify the entry point: CLI, Python API, resume, or retrain.
2. Check the config and backend requirements before proposing commands.
3. Use the workflow reference to map the request to the correct phase or artifact.
4. Use the API reference when you need exact parameter names or return shapes.
5. Use the data-formats reference for dataset layout, split, or package questions.
6. Use the troubleshooting reference for recovery paths and failure messages.

## Core workflow summary

- Phase 1: data understanding, layout detection, task analysis, metric selection.
- Phase 2: data preparation, splitting, optional explicit val/test handling, sampling.
- Phase 3: baseline generation with retry logic.
- Phase 4: hypothesis-driven search over feature and model plans.
- Phase 5: optional final evaluation on a held-out test set.
- Phase 6: package the final model under `work_dir/model/` and archive it.

The workflow may also pause for feedback, resume from checkpoints, or switch into retraining
mode when the user passes an existing model package.

## Common decision points

- If the user provides `train_dataset_uri`, prefer it over deprecated `data_refs`.
- If `test_dataset_uri` is provided, final evaluation is auto-enabled.
- If `is_retrain` is true, validate `original_model_uri` or `original_experiment_id` first.
- If `allowed_model_types` is set on resume, verify it still intersects the checkpointed
  viable model types.
- If the dataset is S3-backed, confirm `external_storage_uri` is available for artifacts.
- If the request mentions Databricks, confirm the Databricks Connect path and required env.
- If the request mentions Keras, remember Plexe sets `KERAS_BACKEND=tensorflow` before imports.

## Bundle ownership

This sub-skill owns the detailed CLI/API, workflow, data format, and troubleshooting references.
The root skill should only route here, not duplicate those details.

